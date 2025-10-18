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


def _process_jsonl_file(file_path: str, target_dir: str) -> Tuple[str, List[Any], bool]:
    """
    Process a single JSONL file.
    
    Returns:
        Tuple of (relative_path, content_array, success)
    """
    try:
        content_array = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    obj = json.loads(line)
                    content_array.append(obj)
                except json.JSONDecodeError as e:
                    log.warning(f"Invalid JSON on line {line_num} in {file_path}: {e}")
                    continue
        
        relative_path = _get_relative_path(file_path, target_dir)
        return relative_path, content_array, True
        
    except Exception as e:
        log.warning(f"Error reading {file_path}: {e}")
        return "", [], False


def _find_json_files(target_dir: str) -> Tuple[List[str], List[str]]:
    """
    Find all JSON and JSONL files in the target directory recursively.
    
    Returns:
        Tuple of (json_files, jsonl_files)
    """
    json_files = []
    jsonl_files = []
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
            elif file.endswith('.jsonl'):
                jsonl_files.append(os.path.join(root, file))
    
    return json_files, jsonl_files


def merge_json_files(target_dir: str, output_path: str) -> Dict[str, Any]:
    """
    Merge all JSON and JSONL files from a directory tree into a single JSON file.
    
    Args:
        target_dir: Directory to scan for JSON/JSONL files
        output_path: Output JSON file path
        
    Returns:
        Dictionary with processing statistics
    """
    if not os.path.exists(target_dir):
        raise ValueError(f"Target directory does not exist: {target_dir}")
    
    if not os.path.isdir(target_dir):
        raise ValueError(f"Target path is not a directory: {target_dir}")
    
    log.info(f"Scanning directory: {target_dir}")
    
    # Find all JSON and JSONL files
    json_files, jsonl_files = _find_json_files(target_dir)
    
    log.info(f"Found {len(json_files)} JSON files and {len(jsonl_files)} JSONL files")
    
    # Process files
    merged_data = {}
    stats = {
        "files_processed": 0,
        "json_count": 0,
        "jsonl_count": 0,
        "errors": 0,
        "output_size": 0
    }
    
    # Process JSON files
    for file_path in json_files:
        relative_path, content, success = _process_json_file(file_path, target_dir)
        stats["files_processed"] += 1
        
        if success:
            merged_data[relative_path] = content
            stats["json_count"] += 1
        else:
            stats["errors"] += 1
    
    # Process JSONL files
    for file_path in jsonl_files:
        relative_path, content_array, success = _process_jsonl_file(file_path, target_dir)
        stats["files_processed"] += 1
        
        if success:
            merged_data[relative_path] = content_array
            stats["jsonl_count"] += 1
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
    
    log.info(f"Merged {stats['json_count']} JSON files and {stats['jsonl_count']} JSONL files")
    log.info(f"Output written to: {output_path} ({stats['output_size']:,} bytes)")
    
    if stats["errors"] > 0:
        log.warning(f"Encountered {stats['errors']} errors during processing")
    
    return stats
