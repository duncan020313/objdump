import json
import os
from typing import Any, Dict, List, Union
from pathlib import Path


def remove_max_depth_reached_recursive(data: Any) -> Any:
    """
    Recursively remove keys with MAX_DEPTH_REACHED values and their children.
    
    Args:
        data: JSON data structure (dict, list, or primitive)
        
    Returns:
        Cleaned data structure with MAX_DEPTH_REACHED keys removed
    """
    if isinstance(data, dict):
        # Create a new dict without MAX_DEPTH_REACHED keys
        cleaned = {}
        for key, value in data.items():
            # Skip keys that have MAX_DEPTH_REACHED as their value
            if value == "[MAX_DEPTH_REACHED]":
                continue
            # Recursively process the value
            cleaned_value = remove_max_depth_reached_recursive(value)
            # Only add the key if the cleaned value is not empty or None
            if cleaned_value is not None and cleaned_value != "":
                cleaned[key] = cleaned_value
        return cleaned
    elif isinstance(data, list):
        # Process each item in the list
        cleaned = []
        for item in data:
            cleaned_item = remove_max_depth_reached_recursive(item)
            # Only add non-empty items
            if cleaned_item is not None and cleaned_item != "":
                cleaned.append(cleaned_item)
        return cleaned
    else:
        # For primitive types, return as-is
        return data


def process_jsonl_file(input_path: str, output_path: str) -> int:
    """
    Process a JSONL file to remove MAX_DEPTH_REACHED entries.
    
    Args:
        input_path: Path to input JSONL file
        output_path: Path to output JSONL file
        
    Returns:
        Number of lines processed
    """
    processed_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Parse JSON line
                data = json.loads(line)
                
                # Remove MAX_DEPTH_REACHED entries
                cleaned_data = remove_max_depth_reached_recursive(data)
                
                # Only write non-empty cleaned data
                if cleaned_data:
                    outfile.write(json.dumps(cleaned_data, ensure_ascii=False) + '\n')
                    processed_count += 1
                    
            except json.JSONDecodeError as e:
                # Skip malformed JSON lines
                print(f"Warning: Skipping malformed JSON line: {e}")
                continue
            except Exception as e:
                # Skip lines that cause other errors
                print(f"Warning: Error processing line: {e}")
                continue
    
    return processed_count


def process_json_file(input_path: str, output_path: str) -> bool:
    """
    Process a JSON file to remove MAX_DEPTH_REACHED entries.
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            data = json.load(infile)
        
        # Remove MAX_DEPTH_REACHED entries
        cleaned_data = remove_max_depth_reached_recursive(data)
        
        # Write cleaned data
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(cleaned_data, outfile, indent=2, ensure_ascii=False)
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}")
        return False
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False


def post_process_dump_files(dump_dir: str, backup: bool = True) -> Dict[str, int]:
    """
    Post-process all JSON/JSONL files in a directory to remove MAX_DEPTH_REACHED entries.
    
    Args:
        dump_dir: Directory containing dump files
        backup: Whether to create backup files before processing
        
    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'jsonl_files_processed': 0,
        'json_files_processed': 0,
        'total_lines_processed': 0,
        'errors': 0
    }
    
    if not os.path.exists(dump_dir):
        print(f"Warning: Directory {dump_dir} does not exist")
        return stats
    
    # Find all JSON and JSONL files
    jsonl_files = list(Path(dump_dir).glob('*.jsonl'))
    json_files = list(Path(dump_dir).glob('*.json'))
    
    # Process JSONL files
    for jsonl_file in jsonl_files:
        try:
            if backup:
                backup_path = str(jsonl_file) + '.backup'
                os.rename(str(jsonl_file), backup_path)
                input_path = backup_path
            else:
                input_path = str(jsonl_file)
            
            # Process the file
            lines_processed = process_jsonl_file(input_path, str(jsonl_file))
            stats['jsonl_files_processed'] += 1
            stats['total_lines_processed'] += lines_processed
            
            # Remove backup if processing was successful
            if backup and os.path.exists(input_path):
                os.remove(input_path)
                
        except Exception as e:
            print(f"Error processing {jsonl_file}: {e}")
            stats['errors'] += 1
    
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
            if process_json_file(input_path, str(json_file)):
                stats['json_files_processed'] += 1
            
            # Remove backup if processing was successful
            if backup and os.path.exists(input_path):
                os.remove(input_path)
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            stats['errors'] += 1
    
    return stats


def main():
    """Command line interface for post-processing dump files."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Post-process JSON dump files to remove MAX_DEPTH_REACHED entries')
    parser.add_argument('dump_dir', help='Directory containing dump files')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dump_dir):
        print(f"Error: Directory {args.dump_dir} does not exist")
        return 1
    
    print(f"Post-processing dump files in {args.dump_dir}")
    stats = post_process_dump_files(args.dump_dir, backup=not args.no_backup)
    
    if args.verbose:
        print(f"Processing complete:")
        print(f"  JSONL files processed: {stats['jsonl_files_processed']}")
        print(f"  JSON files processed: {stats['json_files_processed']}")
        print(f"  Total lines processed: {stats['total_lines_processed']}")
        print(f"  Errors: {stats['errors']}")
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    exit(main())
