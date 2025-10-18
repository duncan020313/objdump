import os
import re
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Dict
from instrumentation.post_processor import post_process_dump_files, process_multiple_directories_by_method


def _cleanup_collection_directory(collection_dir: str, has_test_results: bool) -> None:
    """
    Remove all files and directories except correct/, wrong/, schemas/, and instrumented_methods.json.
    
    Args:
        collection_dir: Directory to clean up
        has_test_results: Whether test results are available (affects which directories to keep)
    """
    log = logging.getLogger("collector")
    
    try:
        for item in os.listdir(collection_dir):
            item_path = os.path.join(collection_dir, item)
            
            # Keep essential directories and files
            if item in ["correct", "wrong", "schemas"]:
                continue
            if item == "instrumented_methods.json":
                continue
            
            # Remove everything else
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    log.debug(f"Removed directory: {item}")
                else:
                    os.remove(item_path)
                    log.debug(f"Removed file: {item}")
            except OSError as e:
                log.warning(f"Failed to remove {item}: {e}")
                
    except OSError as e:
        log.error(f"Failed to list directory {collection_dir}: {e}")


def collect_dumps(work_dir: str, project_id: str, bug_id: str, output_base: str, test_results: Optional[Dict[str, str]] = None) -> str:
    """
    Collect all JSON dump files from the dumps directory and organize them by project/bug ID.
    Separates dump files into correct/ and wrong/ subdirectories based on test results.
    Also copies instrumented methods JSON file if it exists.
    
    Args:
        work_dir: Working directory containing the dumps subdirectory
        project_id: Project identifier (e.g., "Math", "Chart")
        bug_id: Bug identifier (e.g., "1", "2")
        output_base: Base directory for collected dumps
        test_results: Optional dictionary mapping test names to "correct"/"wrong" status
        
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
        
        # Create correct/ and wrong/ subdirectories if test results are available
        if test_results:
            correct_dir = os.path.join(collection_dir, "correct")
            wrong_dir = os.path.join(collection_dir, "wrong")
            os.makedirs(correct_dir, exist_ok=True)
            os.makedirs(wrong_dir, exist_ok=True)
            log.debug(f"Created subdirectories: {correct_dir}, {wrong_dir}")
    except OSError as e:
        raise OSError(f"Failed to create collection directory {collection_dir}: {e}")
    
    # Find all JSON files in dumps directory
    json_files = []
    try:
        for filename in os.listdir(dumps_dir):
            if filename.endswith('.json'):
                json_files.append(filename)
    except OSError as e:
        raise OSError(f"Failed to list files in dumps directory {dumps_dir}: {e}")
    
    # Copy each JSON file to appropriate subdirectory based on test results
    copied_files = []
    for filename in json_files:
        src_path = os.path.join(dumps_dir, filename)
        
        # Determine target directory based on test results
        if test_results:
            # Extract test name from filename (remove .json and convert back from safe name)
            test_name = filename[:-5]  # Remove .json
            # Find matching test in test_results
            test_status = None
            for test, status in test_results.items():
                safe_name = re.sub(r"[^A-Za-z0-9]", "-", test)
                if safe_name == test_name:
                    test_status = status
                    break
            
            if test_status == "correct":
                dst_path = os.path.join(collection_dir, "correct", filename)
            elif test_status == "wrong":
                dst_path = os.path.join(collection_dir, "wrong", filename)
            else:
                # If test not found in results, put in root directory
                dst_path = os.path.join(collection_dir, filename)
                log.warning(f"Test {test_name} not found in test results, placing in root directory")
        else:
            # No test results available, put all files in root directory
            dst_path = os.path.join(collection_dir, filename)
        
        try:
            shutil.copy2(src_path, dst_path)
            copied_files.append(filename)
            log.debug(f"Copied {filename} to {dst_path}")
        except OSError as e:
            log.error(f"Failed to copy {filename}: {e}")
            # Continue with other files even if one fails
    
    # Also copy instrumented methods JSON file if it exists
    instrumented_methods_file = os.path.join(work_dir, "instrumented_methods.json")
    if os.path.exists(instrumented_methods_file):
        try:
            dst_path = os.path.join(collection_dir, "instrumented_methods.json")
            shutil.copy2(instrumented_methods_file, dst_path)
            copied_files.append("instrumented_methods.json")
            log.debug(f"Copied instrumented_methods.json to {dst_path}")
        except OSError as e:
            log.error(f"Failed to copy instrumented_methods.json: {e}")
    
    if not copied_files:
        log.warning(f"No files found to collect in {dumps_dir}")
        return collection_dir
    
    log.info(f"Collected {len(copied_files)} files to {collection_dir}")
    
    # Post-process the collected files to remove MAX_DEPTH_REACHED entries
    try:
        log.info("Post-processing collected files to remove MAX_DEPTH_REACHED entries...")
        
        if test_results:
            # Process both correct and wrong directories with unified schema generation
            correct_dir = os.path.join(collection_dir, "correct")
            wrong_dir = os.path.join(collection_dir, "wrong")
            schemas_output_dir = os.path.join(collection_dir, "schemas")
            
            # Collect directories that exist
            directories_to_process = []
            if os.path.exists(correct_dir):
                directories_to_process.append(correct_dir)
            if os.path.exists(wrong_dir):
                directories_to_process.append(wrong_dir)
            
            if directories_to_process:
                log.info(f"Processing {len(directories_to_process)} directories for unified schema generation")
                stats = process_multiple_directories_by_method(
                    directories_to_process, 
                    schemas_output_dir, 
                    backup=True
                )
                log.info(f"Unified post-processing complete: {stats['json_files_processed']} JSON files, "
                        f"{stats['total_lines_processed']} lines processed, "
                        f"{stats['schemas_generated']} schemas generated")
                if stats['errors'] > 0:
                    log.warning(f"Post-processing had {stats['errors']} errors")
            else:
                log.warning("No correct/ or wrong/ directories found for schema generation")
        else:
            # Post-process root directory if no test results
            stats = post_process_dump_files(collection_dir, backup=True)
            log.info(f"Post-processing complete: {stats['json_files_processed']} JSON files, "
                    f"{stats['total_lines_processed']} lines processed")
            if stats['errors'] > 0:
                log.warning(f"Post-processing had {stats['errors']} errors")
        
        # Clean up: Remove all files and directories except correct/, wrong/, schemas/, and instrumented_methods.json
        log.info("Cleaning up collection directory...")
        _cleanup_collection_directory(collection_dir, test_results is not None)
        
    except Exception as e:
        log.error(f"Post-processing failed: {e}")
        # Don't fail the collection process if post-processing fails
    
    return collection_dir


def collect_dumps_safe(work_dir: str, project_id: str, bug_id: str, output_base: str, test_results: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Safe version of collect_dumps that returns None on failure instead of raising exceptions.
    
    Args:
        work_dir: Working directory containing the dumps subdirectory
        project_id: Project identifier
        bug_id: Bug identifier  
        output_base: Base directory for collected dumps
        test_results: Optional dictionary mapping test names to "correct"/"wrong" status
        
    Returns:
        Path to collection directory if successful, None if failed
    """
    try:
        return collect_dumps(work_dir, project_id, bug_id, output_base, test_results)
    except Exception as e:
        log = logging.getLogger("collector")
        log.error(f"Failed to collect dumps: {e}")
        return None
