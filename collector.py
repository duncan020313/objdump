import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional


def collect_dumps(work_dir: str, project_id: str, bug_id: str, output_base: str) -> str:
    """
    Collect all JSONL dump files from the dumps directory and organize them by project/bug ID.
    
    Args:
        work_dir: Working directory containing the dumps subdirectory
        project_id: Project identifier (e.g., "Math", "Chart")
        bug_id: Bug identifier (e.g., "1", "2")
        output_base: Base directory for collected dumps
        
    Returns:
        Path to the collection directory where files were copied
        
    Raises:
        FileNotFoundError: If dumps directory doesn't exist
        OSError: If unable to create output directories or copy files
    """
    log = logging.getLogger("collector")
    
    # Source directory containing dump files
    dumps_dir = os.path.join(work_dir, "dumps")
    if not os.path.exists(dumps_dir):
        raise FileNotFoundError(f"Dumps directory not found: {dumps_dir}")
    
    # Target directory: <output_base>/<project_id>/<bug_id>/
    collection_dir = os.path.join(output_base, project_id, bug_id)
    
    try:
        # Create target directory structure
        os.makedirs(collection_dir, exist_ok=True)
        log.debug(f"Created collection directory: {collection_dir}")
    except OSError as e:
        raise OSError(f"Failed to create collection directory {collection_dir}: {e}")
    
    # Find all JSONL files in dumps directory
    jsonl_files = []
    try:
        for filename in os.listdir(dumps_dir):
            if filename.endswith('.jsonl'):
                jsonl_files.append(filename)
    except OSError as e:
        raise OSError(f"Failed to list files in dumps directory {dumps_dir}: {e}")
    
    if not jsonl_files:
        log.warning(f"No JSONL files found in {dumps_dir}")
        return collection_dir
    
    # Copy each JSONL file to collection directory
    copied_files = []
    for filename in jsonl_files:
        src_path = os.path.join(dumps_dir, filename)
        dst_path = os.path.join(collection_dir, filename)
        
        try:
            shutil.copy2(src_path, dst_path)
            copied_files.append(filename)
            log.debug(f"Copied {filename} to {dst_path}")
        except OSError as e:
            log.error(f"Failed to copy {filename}: {e}")
            # Continue with other files even if one fails
    
    log.info(f"Collected {len(copied_files)} dump files to {collection_dir}")
    return collection_dir


def collect_dumps_safe(work_dir: str, project_id: str, bug_id: str, output_base: str) -> Optional[str]:
    """
    Safe version of collect_dumps that returns None on failure instead of raising exceptions.
    
    Args:
        work_dir: Working directory containing the dumps subdirectory
        project_id: Project identifier
        bug_id: Bug identifier  
        output_base: Base directory for collected dumps
        
    Returns:
        Path to collection directory if successful, None if failed
    """
    try:
        return collect_dumps(work_dir, project_id, bug_id, output_base)
    except Exception as e:
        log = logging.getLogger("collector")
        log.error(f"Failed to collect dumps: {e}")
        return None
