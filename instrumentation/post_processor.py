import json
import argparse
import logging
from logging_setup import configure_logging
import os
import re
from typing import Any, Dict, List, Union, Optional, Set
from pathlib import Path
from genson import SchemaBuilder

configure_logging()
log = logging.getLogger("post_process_dump_files")


MAX_DEPTH_MARKER = "[MAX_DEPTH_REACHED]"
CYCLE_MARKER = "[CYCLE_DETECTED]"
SER_ERROR_PREFIX = "[SERIALIZATION_ERROR:"


def _is_special_numeric_string(value: Any) -> bool:
    """Return True if value is a string representing NaN or (±)Infinity.

    This aligns with Java's Double/Float string forms: "NaN", "Infinity", "-Infinity".
    Case-insensitive matching is also supported.
    """
    if not isinstance(value, str):
        return False
    v = value.strip()
    lower = v.lower()
    return lower in {"nan", "infinity", "+infinity", "-infinity"}


def _convert_special_numeric_strings_to_int(data: Any) -> Any:
    """Recursively convert special numeric strings (NaN/Infinity) to int for schema inference.

    We keep original cleaned JSON unchanged; this is only for feeding SchemaBuilder
    so fields don't become union of integer|string when special values appear.
    """
    if _is_special_numeric_string(data):
        return 0
    if isinstance(data, list):
        return [_convert_special_numeric_strings_to_int(item) for item in data]
    if isinstance(data, dict):
        return {k: _convert_special_numeric_strings_to_int(v) for k, v in data.items()}
    return data


def sanitize_field_name(field_name: str) -> str:
    """
    Sanitize field name to conform to Java identifier rules: [a-zA-Z_][a-zA-Z0-9_]*

    Args:
        field_name: Original field name

    Returns:
        Sanitized field name, or empty string if no valid characters remain
    """
    if not isinstance(field_name, str):
        field_name = str(field_name)

    # Remove all characters not in [a-zA-Z0-9_]
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', field_name)
    # Remove leading digits to ensure it starts with [a-zA-Z_]
    sanitized = re.sub(r'^[0-9]+', '', sanitized)

    return sanitized

def remove_max_depth_reached_recursive(data: Any) -> Any:
    """
    Recursively remove keys with MAX_DEPTH_REACHED or CYCLE_DETECTED values and their children.
    Also removes empty arrays and objects, and SERIALIZATION_ERROR entries.
    Sanitizes field names to conform to Java identifier rules.

    Args:
        data: JSON data structure (dict, list, or primitive)

    Returns:
        Cleaned data structure with MAX_DEPTH_REACHED keys and empty containers removed,
        and field names sanitized
    """
    if isinstance(data, dict):
        # Create a new dict without MAX_DEPTH_REACHED keys and with sanitized field names
        cleaned = {}
        used_keys: Set[str] = set()

        for key, value in data.items():
            # Skip keys that have MAX_DEPTH_REACHED or SERIALIZATION_ERROR as their value
            if value == MAX_DEPTH_MARKER or value == CYCLE_MARKER or value == [] or value == {}:
                continue
            if isinstance(value, str) and value.startswith(SER_ERROR_PREFIX):
                continue

            # Recursively process the value
            cleaned_value = remove_max_depth_reached_recursive(value)

            # Only add the key if the cleaned value is not empty or None
            is_error = isinstance(cleaned_value, str) and cleaned_value.startswith(SER_ERROR_PREFIX)
            if (
                cleaned_value is not None
                and cleaned_value != ""
                and cleaned_value != MAX_DEPTH_MARKER
                and cleaned_value != CYCLE_MARKER
                and cleaned_value != []
                and cleaned_value != {}
                and not is_error
            ):
                # Sanitize the key
                sanitized_key = sanitize_field_name(key)

                # Fall back to "field_<original_key>" if sanitization results in empty string
                if not sanitized_key:
                    sanitized_key = f"field_{key}"

                # Handle key collision by adding suffix
                final_key = sanitized_key
                counter = 1
                while final_key in used_keys:
                    final_key = f"{sanitized_key}_{counter}"
                    counter += 1

                used_keys.add(final_key)
                cleaned[final_key] = cleaned_value

        return cleaned
    elif isinstance(data, list):
        # Process each item in the list
        cleaned = []
        for item in data:
            cleaned_item = remove_max_depth_reached_recursive(item)
            # Only add non-empty items
            is_error = isinstance(cleaned_item, str) and cleaned_item.startswith(SER_ERROR_PREFIX)
            if (
                cleaned_item is not None
                and cleaned_item != ""
                and cleaned_item != MAX_DEPTH_MARKER
                and cleaned_item != CYCLE_MARKER
                and cleaned_item != []
                and cleaned_item != {}
                and not is_error
            ):
                cleaned.append(cleaned_item)
        return cleaned
    else:
        # For primitive types, return as-is
        return data


def _write_schema_file(schema_output_path: str, schema_obj: Dict[str, Any]) -> None:
    """Write a JSON Schema file with $schema set to the proper URL."""
    with open(schema_output_path, 'w', encoding='utf-8') as sf:
        json.dump(schema_obj, sf, indent=4, ensure_ascii=False, sort_keys=True)


def _sanitize_path_for_filesystem(path: str) -> str:
    """Sanitize a file path to be safe for filesystem usage."""
    # Replace problematic characters with underscores
    sanitized = re.sub(r'[<>:"|?*]', '_', path)
    # Replace multiple slashes with single slashes
    sanitized = re.sub(r'/+', '_', sanitized)
    # Remove leading/trailing slashes and dots
    sanitized = sanitized.strip('/.')
    return sanitized


def process_dump_directory_by_method(dump_dir: str, backup: bool = True) -> Dict[str, int]:
    """
    Process all JSON files in a directory and generate schemas grouped by method.

    Args:
        dump_dir: Directory containing dump files
        backup: Whether to create backup files before processing

    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'json_files_processed': 0,
        'total_lines_processed': 0,
        'methods_processed': 0,
        'schemas_generated': 0,
        'errors': 0
    }

    if not os.path.exists(dump_dir):
        log.warning(f"Directory {dump_dir} does not exist")
        return stats

    # Find all JSON files, excluding schema files
    json_files = [f for f in Path(dump_dir).glob('*.json') if 'schema' not in f.name.lower()]

    # Group records by (file_path, method_signature, phase)
    method_records: Dict[tuple, List[Dict[str, Any]]] = {}

    # Process each JSON file
    for json_file in json_files:
        if backup:
            backup_path = str(json_file) + '.backup'
            os.rename(str(json_file), backup_path)
            input_path = backup_path
        else:
            input_path = str(json_file)

        # Read JSON array
        with open(input_path, 'r', encoding='utf-8') as infile:
            data_array = json.load(infile)

        # Process each record in the array
        cleaned_records = []
        for data in data_array:
            try:
                # Remove MAX_DEPTH_REACHED and CYCLE_DETECTED entries
                cleaned_data = remove_max_depth_reached_recursive(data)

                # Extract method metadata
                method_signature = cleaned_data.get("method_signature", "unknown")
                file_path = cleaned_data.get("file_path", "unknown")
                phase = cleaned_data.get("phase")

                if phase in ("entry", "exit"):
                    key = (file_path, method_signature, phase)
                    if key not in method_records:
                        method_records[key] = []
                    method_records[key].append(cleaned_data)
                    stats['total_lines_processed'] += 1

                cleaned_records.append(cleaned_data)

            except Exception as e:
                log.warning(f"Error processing record in {json_file}: {e}")
                continue

        # Write cleaned data back to original file as JSON array
        with open(str(json_file), 'w', encoding='utf-8') as outfile:
            json.dump(cleaned_records, outfile, ensure_ascii=False, indent=2, sort_keys=True)

        stats['json_files_processed'] += 1

        # Remove backup if processing was successful
        if backup and os.path.exists(input_path):
            os.remove(input_path)
    # Generate schemas for each method
    schemas_dir = os.path.join(dump_dir, "schemas")
    os.makedirs(schemas_dir, exist_ok=True)

    # Group by (file_path, method_signature) to create entry and exit schemas
    method_groups: Dict[tuple, Dict[str, List[Dict[str, Any]]]] = {}
    for (file_path, method_signature, phase), records in method_records.items():
        key = (file_path, method_signature)
        if key not in method_groups:
            method_groups[key] = {}
        method_groups[key][phase] = records

    for (file_path, method_signature), phase_records in method_groups.items():
        try:
            # Sanitize paths for filesystem
            safe_file_path = _sanitize_path_for_filesystem(file_path)
            safe_method_signature = _sanitize_path_for_filesystem(method_signature)

            # Create directory structure: schemas/<file-path>/<method-signature>/
            method_dir = os.path.join(schemas_dir, safe_file_path, safe_method_signature)
            os.makedirs(method_dir, exist_ok=True)

            # Generate schemas for each phase
            for phase in ("entry", "exit"):
                if phase in phase_records and phase_records[phase]:
                    builder = SchemaBuilder()
                    for record in phase_records[phase]:
                        builder.add_object(_convert_special_numeric_strings_to_int(record))

                    schema_obj = builder.to_schema()
                    schema_path = os.path.join(method_dir, f"{phase}.schema.json")
                    _write_schema_file(schema_path, schema_obj)
                    stats['schemas_generated'] += 1

            stats['methods_processed'] += 1

        except Exception as e:
            log.error(f"Error generating schema for {file_path}::{method_signature}: {e}")
            stats['errors'] += 1

    return stats


def process_multiple_directories_by_method(
    dump_dirs: List[str],
    schemas_output_dir: str,
    backup: bool = True
) -> Dict[str, int]:
    """
    Process JSON files from multiple directories and generate unified schemas.

    Each directory is processed to remove MAX_DEPTH_REACHED entries (in-place),
    then all records are combined to generate unified schemas in a separate location.

    Args:
        dump_dirs: List of directories containing dump files
        schemas_output_dir: Directory where schemas should be written
        backup: Whether to create backup files before processing

    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'json_files_processed': 0,
        'total_lines_processed': 0,
        'methods_processed': 0,
        'schemas_generated': 0,
        'errors': 0
    }

    # Group records by (file_path, method_signature, phase) across all directories
    method_records: Dict[tuple, List[Dict[str, Any]]] = {}

    # Process each directory
    for dump_dir in dump_dirs:
        if not os.path.exists(dump_dir):
            log.warning(f"Directory {dump_dir} does not exist, skipping")
            continue

        # Find all JSON files, excluding schema files
        json_files = [f for f in Path(dump_dir).glob('*.json') if 'schema' not in f.name.lower()]

        # Process each JSON file in this directory
        for json_file in json_files:
            if backup:
                backup_path = str(json_file) + '.backup'
                os.rename(str(json_file), backup_path)
                input_path = backup_path
            else:
                input_path = str(json_file)

            # Read JSON array
            with open(input_path, 'r', encoding='utf-8') as infile:
                file_contents = infile.read()
                if not file_contents.strip():
                    continue
                try:
                    data_array = json.loads(file_contents)
                except json.JSONDecodeError as e:
                    log.error(f"Invalid JSON in {json_file}: {e}")
                    continue

            # Process each record in the array
            cleaned_records = []
            for data in data_array:
                try:
                    # Remove MAX_DEPTH_REACHED and CYCLE_DETECTED entries
                    cleaned_data = remove_max_depth_reached_recursive(data)

                    # Extract method metadata
                    method_signature = cleaned_data.get("method_signature", "unknown")
                    file_path = cleaned_data.get("file_path", "unknown")
                    phase = cleaned_data.get("phase")

                    if phase in ("entry", "exit"):
                        key = (file_path, method_signature, phase)
                        if key not in method_records:
                            method_records[key] = []
                        method_records[key].append(cleaned_data)
                        stats['total_lines_processed'] += 1

                    cleaned_records.append(cleaned_data)

                except Exception as e:
                    log.warning(f"Error processing record in {json_file}: {e}")
                    continue

            # Write cleaned data back to original file as JSON array
            with open(str(json_file), 'w', encoding='utf-8') as outfile:
                json.dump(cleaned_records, outfile, ensure_ascii=False, indent=2, sort_keys=True)

            stats['json_files_processed'] += 1

            # Remove backup if processing was successful
            if backup and os.path.exists(input_path):
                os.remove(input_path)
    # Generate unified schemas for all methods
    os.makedirs(schemas_output_dir, exist_ok=True)

    # Group by (file_path, method_signature) to create entry and exit schemas
    method_groups: Dict[tuple, Dict[str, List[Dict[str, Any]]]] = {}
    for (file_path, method_signature, phase), records in method_records.items():
        key = (file_path, method_signature)
        if key not in method_groups:
            method_groups[key] = {}
        method_groups[key][phase] = records

    for (file_path, method_signature), phase_records in method_groups.items():
        try:
            # Sanitize paths for filesystem
            safe_file_path = _sanitize_path_for_filesystem(file_path)
            safe_method_signature = _sanitize_path_for_filesystem(method_signature)

            # Create directory structure: schemas/<file-path>/<method-signature>/
            method_dir = os.path.join(schemas_output_dir, safe_file_path, safe_method_signature)
            os.makedirs(method_dir, exist_ok=True)

            # Generate schemas for each phase
            for phase in ("entry", "exit"):
                if phase in phase_records and phase_records[phase]:
                    builder = SchemaBuilder()
                    for record in phase_records[phase]:
                        builder.add_object(_convert_special_numeric_strings_to_int(record))

                    schema_obj = builder.to_schema()
                    schema_path = os.path.join(method_dir, f"{phase}.schema.json")
                    _write_schema_file(schema_path, schema_obj)
                    stats['schemas_generated'] += 1

            stats['methods_processed'] += 1

        except Exception as e:
            log.error(f"Error generating schema for {file_path}::{method_signature}: {e}")
            stats['errors'] += 1

    return stats


def process_json_file(input_path: str, output_path: str, *, emit_schema: bool = True) -> int:
    """
    Process a JSON file to remove MAX_DEPTH_REACHED and CYCLE_DETECTED entries.

    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file

    Returns:
        Number of records processed
    """
    processed_count = 0
    builders: Dict[str, Any] = {}

    try:
        # Read JSON array
        with open(input_path, 'r', encoding='utf-8') as infile:
            file_contents = infile.read()
            if not file_contents.strip():
                return processed_count
            data_array = json.loads(file_contents)

        # Process each record in the array
        cleaned_records = []
        for data in data_array:
            try:
                # Remove MAX_DEPTH_REACHED and CYCLE_DETECTED entries
                cleaned_data = remove_max_depth_reached_recursive(data)
                cleaned_records.append(cleaned_data)
                processed_count += 1

                # Feed schema builders by phase if requested
                if emit_schema and isinstance(cleaned_data, dict):
                    phase = cleaned_data.get("phase")
                    if phase in ("entry", "exit"):
                        if phase not in builders:
                            builder = SchemaBuilder()
                            builders[phase] = builder
                        builder = builders.get(phase)
                        if builder is not None:
                            # genson accepts dicts directly
                            builder.add_object(_convert_special_numeric_strings_to_int(cleaned_data))

            except Exception as e:
                # Skip records that cause errors
                log.warning(f"Error processing record: {e}")
                continue

        # Write cleaned data as JSON array
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(cleaned_records, outfile, ensure_ascii=False, indent=2, sort_keys=True)

    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in {input_path}: {e}")
        return 0
    except Exception as e:
        log.error(f"Error processing {input_path}: {e}")
        return 0

    # Emit per-phase schemas next to the JSON file
    if emit_schema and builders:
        for phase, builder in builders.items():
            schema_obj = builder.to_schema()
            schema_path = f"{output_path}.{phase}.schema.json"
            _write_schema_file(schema_path, schema_obj)
    return processed_count


def process_single_json_file(input_path: str, output_path: str, *, emit_schema: bool = True) -> bool:
    """
    Process a single JSON file to remove MAX_DEPTH_REACHED and CYCLE_DETECTED entries.

    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file

    Returns:
        True if processing was successful, False otherwise
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            data = json.load(infile)

        # Remove MAX_DEPTH_REACHED and CYCLE_DETECTED entries
        cleaned_data = remove_max_depth_reached_recursive(data)

        # Write cleaned data
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(cleaned_data, outfile, indent=4, ensure_ascii=False, sort_keys=True)

        # Optionally emit schema next to the JSON file
        if emit_schema:
            builder = SchemaBuilder()
            if isinstance(cleaned_data, list):
                for item in cleaned_data:
                    builder.add_object(_convert_special_numeric_strings_to_int(item))
            else:
                builder.add_object(_convert_special_numeric_strings_to_int(cleaned_data))
            schema_obj = builder.to_schema()
            schema_path = f"{output_path}.schema.json"
            _write_schema_file(schema_path, schema_obj)

        return True

    except json.JSONDecodeError as e:
        log.error(f"Error: Invalid JSON in {input_path}: {e}")
        return False
    except Exception as e:
        log.error(f"Error processing {input_path}: {e}")
        return False


def post_process_dump_files(dump_dir: str, backup: bool = True, *, emit_schema: bool = True) -> Dict[str, int]:
    """
    Post-process all JSON files in a directory to remove MAX_DEPTH_REACHED and CYCLE_DETECTED entries.
    Uses method-level schema generation when emit_schema is True.

    Args:
        dump_dir: Directory containing dump files
        backup: Whether to create backup files before processing
        emit_schema: Whether to generate schemas (uses method-level grouping if True)

    Returns:
        Dictionary with processing statistics
    """
    if emit_schema:
        # Use method-level schema generation
        return process_dump_directory_by_method(dump_dir, backup)

    # Fall back to original per-file processing
    stats = {
        'json_files_processed': 0,
        'total_lines_processed': 0,
        'errors': 0
    }

    if not os.path.exists(dump_dir):
        log.warning(f"Directory {dump_dir} does not exist")
        return stats

    # Find all JSON files, excluding schema files
    json_files = [f for f in Path(dump_dir).glob('*.json') if 'schema' not in f.name.lower()]

    # Process JSON files
    for json_file in json_files:
        try:
            if backup:
                backup_path = str(json_file) + '.backup'
                os.rename(str(json_file), backup_path)
                input_path = backup_path
            else:
                input_path = str(json_file)

            # Process the file
            lines_processed = process_json_file(input_path, str(json_file), emit_schema=emit_schema)
            stats['json_files_processed'] += 1
            stats['total_lines_processed'] += lines_processed

            # Remove backup if processing was successful
            if backup and os.path.exists(input_path):
                os.remove(input_path)

        except Exception as e:
            log.error(f"Error processing {json_file}: {e}")
            stats['errors'] += 1


    return stats


def main():
    """Command line interface for post-processing dump files."""
    parser = argparse.ArgumentParser(description='Post-process JSON dump files to remove MAX_DEPTH_REACHED entries and optionally emit JSON Schemas')
    parser.add_argument('dump_dir', help='Directory containing dump files')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-schema', action='store_true', help='Do not generate JSON Schema files')
    args = parser.parse_args()

    if not os.path.exists(args.dump_dir):
        log.error(f"Error: Directory {args.dump_dir} does not exist")
        return 1

    log.info(f"Post-processing dump files in {args.dump_dir}")
    stats = post_process_dump_files(
        args.dump_dir,
        backup=not args.no_backup,
        emit_schema=not args.no_schema,
    )

    if args.verbose:
        log.info(f"Processing complete:")
        if 'methods_processed' in stats:
            # Method-level processing stats
            log.info(f"  JSON files processed: {stats['json_files_processed']}")
            log.info(f"  Total lines processed: {stats['total_lines_processed']}")
            log.info(f"  Methods processed: {stats['methods_processed']}")
            log.info(f"  Schemas generated: {stats['schemas_generated']}")
            log.info(f"  Errors: {stats['errors']}")
        else:
            # Original per-file processing stats
            log.info(f"  JSON files processed: {stats['json_files_processed']}")
            log.info(f"  Total lines processed: {stats['total_lines_processed']}")
            log.info(f"  Errors: {stats['errors']}")

    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    exit(main())
