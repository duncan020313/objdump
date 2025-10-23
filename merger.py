"""
JSON file merger module for combining multiple JSON/JSONL files into a single JSON file.
"""

import json
import os
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

log = logging.getLogger("merger")


def _get_relative_path(file_path: str, target_dir: str) -> str:
    """Get relative path from target directory."""
    return os.path.relpath(file_path, target_dir)


def _create_nested_structure(relative_path: str, content: Any) -> Dict[str, Any]:
    """
    Create nested structure from path components.

    Args:
        relative_path: Relative path from target directory
        content: JSON content to store at the end of the path

    Returns:
        Nested dictionary structure
    """
    # Split path into components
    path_parts = relative_path.split(os.sep)

    # Create nested structure
    result = {}
    current = result

    # Navigate through path components, creating nested dicts
    for part in path_parts[:-1]:  # All parts except the last one
        if part not in current:
            current[part] = {}
        current = current[part]

    # Set the content at the final level
    current[path_parts[-1]] = content

    return result


def _merge_nested_dict(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    Recursively merge source dictionary into target dictionary.

    Args:
        target: Target dictionary to merge into
        source: Source dictionary to merge from
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # Both are dictionaries, merge recursively
            _merge_nested_dict(target[key], value)
        else:
            # Replace or add the value
            target[key] = value


def _process_json_file(file_path: str, target_dir: str) -> Tuple[str, Any, bool]:
    """
    Process a single JSON file.

    Returns:
        Tuple of (relative_path, content, success)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)

        relative_path = _get_relative_path(file_path, target_dir)
        return relative_path, content, True

    except json.JSONDecodeError as e:
        log.warning(f"Invalid JSON in {file_path}: {e}")
        return "", None, False
    except Exception as e:
        log.warning(f"Error reading {file_path}: {e}")
        return "", None, False


def _find_json_files(target_dir: str) -> List[str]:
    """
    Find all JSON files in the target directory recursively.

    Returns:
        List of JSON file paths
    """
    json_files = []

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))

    return json_files


def merge_json_files(target_dir: str, output_path: str) -> Dict[str, Any]:
    """
    Merge all JSON files from a directory tree into a single JSON file.

    Args:
        target_dir: Directory to scan for JSON files
        output_path: Output JSON file path

    Returns:
        Dictionary with processing statistics
    """
    if not os.path.exists(target_dir):
        raise ValueError(f"Target directory does not exist: {target_dir}")

    if not os.path.isdir(target_dir):
        raise ValueError(f"Target path is not a directory: {target_dir}")

    log.info(f"Scanning directory: {target_dir}")

    # Find all JSON files
    json_files = _find_json_files(target_dir)

    log.info(f"Found {len(json_files)} JSON files")

    # Process files
    merged_data = {}
    stats = {
        "files_processed": 0,
        "json_count": 0,
        "errors": 0,
        "output_size": 0
    }

    # Process JSON files
    for file_path in json_files:
        relative_path, content, success = _process_json_file(file_path, target_dir)
        stats["files_processed"] += 1

        if success:
            # Create nested structure from path
            nested_structure = _create_nested_structure(relative_path, content)

            # Merge nested structure into merged_data
            _merge_nested_dict(merged_data, nested_structure)
            stats["json_count"] += 1
        else:
            stats["errors"] += 1

    # Write merged data to output file
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False, sort_keys=True)

    # Get output file size
    stats["output_size"] = os.path.getsize(output_path)

    log.info(f"Merged {stats['json_count']} JSON files")
    log.info(f"Output written to: {output_path} ({stats['output_size']:,} bytes)")

    if stats["errors"] > 0:
        log.warning(f"Encountered {stats['errors']} errors during processing")

    return stats
