"""Bug classification module for Defects4J projects.

This module provides functionality to classify bugs as functional or exceptional
based on their root cause error types.
"""

from typing import List, Dict, Any, Set
import csv
import json
import os
import defects4j
import logging
log = logging.getLogger(__name__)

def load_nl2postcond_bugs(json_path: str = "defects4j_nl2postcond_bugs.json") -> Dict[str, Set[str]]:
    """Load nl2postcond bug IDs from JSON file.
    
    Args:
        json_path: Path to the JSON file containing nl2postcond bugs
        
    Returns:
        Dictionary mapping project names to sets of bug IDs (as strings)
    """
    # Get the directory where this module is located
    module_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(module_dir, json_path)
    
    if not os.path.exists(full_path):
        log.warning(f"nl2postcond bugs file not found: {full_path}")
        return {}
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Convert lists to sets of strings
            return {project: set(bug_ids) for project, bug_ids in data.items()}
    except Exception as e:
        log.error(f"Error loading nl2postcond bugs from {full_path}: {e}")
        return {}

def classify_bugs_batch(project_id: str, bug_ids: List[int], max_workers: int = 4) -> List[Dict[str, Any]]:
    """Classify multiple bugs for a project in parallel.

    Args:
        project_id: Defects4J project ID (e.g., "Math")
        bug_ids: List of bug IDs to classify
        max_workers: Maximum number of parallel workers

    Returns:
        List of classification results
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Load nl2postcond bugs
    nl2postcond_bugs = load_nl2postcond_bugs()
    nl2postcond_set = nl2postcond_bugs.get(project_id, set())

    results = []

    def classify_single_bug(bug_id: int) -> Dict[str, Any]:
        bug_info = defects4j.classify_bug(project_id, str(bug_id))
        if bug_info:
            return bug_info
        else:
            return {
                "project": project_id,
                "bug_id": str(bug_id),
                "type": "error",
                "error": "Failed to retrieve bug information"
            }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(classify_single_bug, bug_id) for bug_id in bug_ids]

        for future in as_completed(futures):
            try:
                result = future.result()
                # Add nl2postcond flag
                result["in_nl2postcond"] = result.get("bug_id", "") in nl2postcond_set
                results.append(result)
            except Exception as e:
                error_result = {
                    "project": project_id,
                    "bug_id": "?",
                    "type": "error",
                    "error": str(e),
                    "in_nl2postcond": False
                }
                results.append(error_result)

    return results


def write_classification_csv(file_path_or_buffer, results: List[Dict[str, Any]]) -> None:
    """Write classification results to CSV file or buffer.

    Args:
        file_path_or_buffer: Path to output CSV file or StringIO buffer
        results: List of classification results
    """
    if not results:
        return

    # Define CSV columns
    fieldnames = [
        "project", "bug_id", "type", "bug_report_id", "revision_id",
        "revision_date", "bug_report_url", "root_causes_count",
        "modified_sources_count", "root_causes", "modified_sources", "in_nl2postcond", "error"
    ]

    # Handle both file paths and StringIO objects
    if isinstance(file_path_or_buffer, str):
        with open(file_path_or_buffer, 'w', newline='', encoding='utf-8') as csvfile:
            _write_csv_content(csvfile, fieldnames, results)
    else:
        _write_csv_content(file_path_or_buffer, fieldnames, results)


def _write_csv_content(csvfile, fieldnames: List[str], results: List[Dict[str, Any]]) -> None:
    """Helper function to write CSV content."""
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for result in results:
        # Flatten the result for CSV
        csv_row = {
            "project": result.get("project", ""),
            "bug_id": result.get("bug_id", ""),
            "type": result.get("type", ""),
            "bug_report_id": result.get("bug_report_id", ""),
            "revision_id": result.get("revision_id", ""),
            "revision_date": result.get("revision_date", ""),
            "bug_report_url": result.get("bug_report_url", ""),
            "root_causes_count": len(result.get("root_causes", [])),
            "modified_sources_count": len(result.get("modified_sources", [])),
            "root_causes": "; ".join([f"{rc['test']}: {rc['error']}" for rc in result.get("root_causes", [])]),
            "modified_sources": "; ".join(result.get("modified_sources", [])),
            "in_nl2postcond": result.get("in_nl2postcond", False),
            "error": result.get("error", "")
        }
        writer.writerow(csv_row)


def write_classification_markdown(file_path: str, results: List[Dict[str, Any]]) -> None:
    """Write classification results to markdown table file.

    Args:
        file_path: Path to output markdown file
        results: List of classification results
    """
    if not results:
        return

    with open(file_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# Bug Classification Results\n\n")
        f.write(f"Total bugs classified: {len(results)}\n\n")

        # Count by type
        functional_count = sum(1 for r in results if r.get("type") == "functional")
        exceptional_count = sum(1 for r in results if r.get("type") == "exceptional")
        error_count = sum(1 for r in results if r.get("type") == "error")
        nl2postcond_count = sum(1 for r in results if r.get("in_nl2postcond", False))

        f.write("## Summary\n\n")
        f.write(f"- **Functional bugs**: {functional_count}\n")
        f.write(f"- **Exceptional bugs**: {exceptional_count}\n")
        f.write(f"- **Errors**: {error_count}\n")
        f.write(f"- **NL2 Postcond bugs**: {nl2postcond_count}\n\n")

        # Write table
        f.write("## Classification Results\n\n")
        f.write("| Project | Bug ID | Type | Bug Report | Root Causes | Modified Sources | NL2 |\n")
        f.write("|---------|--------|------|------------|-------------|------------------|-----|\n")

        for result in results:
            project = result.get("project", "")
            bug_id = result.get("bug_id", "")
            bug_type = result.get("type", "")
            bug_report = result.get("bug_report_id", "")

            # Format root causes
            root_causes = result.get("root_causes", [])
            if root_causes:
                root_causes_str = f"{len(root_causes)} cause(s)"
                if len(root_causes) == 1:
                    root_causes_str = f"1: {root_causes[0]['test']}"
                elif len(root_causes) <= 3:
                    root_causes_str = "; ".join([f"{i+1}: {rc['test']}" for i, rc in enumerate(root_causes)])
            else:
                root_causes_str = "None"

            # Format modified sources
            modified_sources = result.get("modified_sources", [])
            if modified_sources:
                if len(modified_sources) == 1:
                    modified_sources_str = modified_sources[0]
                elif len(modified_sources) <= 3:
                    modified_sources_str = "; ".join(modified_sources)
                else:
                    modified_sources_str = f"{len(modified_sources)} class(es)"
            else:
                modified_sources_str = "None"

            # Escape pipe characters in content
            root_causes_str = root_causes_str.replace("|", "\\|")
            modified_sources_str = modified_sources_str.replace("|", "\\|")
            
            # NL2 indicator
            nl2_indicator = "Yes" if result.get("in_nl2postcond", False) else "No"

            f.write(f"| {project} | {bug_id} | {bug_type} | {bug_report} | {root_causes_str} | {modified_sources_str} | {nl2_indicator} |\n")

        f.write("\n")

        # Write detailed error information if any
        error_results = [r for r in results if r.get("type") == "error"]
        if error_results:
            f.write("## Errors\n\n")
            for result in error_results:
                f.write(f"- **{result.get('project', '')}-{result.get('bug_id', '')}**: {result.get('error', '')}\n")
            f.write("\n")


def classify_projects(projects: List[str], max_bugs_per_project: int, workers: int) -> List[Dict[str, Any]]:
    """Classify bugs for multiple projects.

    Args:
        projects: List of project names
        max_bugs_per_project: Maximum bugs per project (0 = no limit)
        workers: Number of parallel workers

    Returns:
        List of classification results for all projects
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_results: List[Dict[str, Any]] = []

    def classify_project_bugs(project: str) -> List[Dict[str, Any]]:
        # Get all available bugs for the project
        bug_ids = defects4j.list_bug_ids(project)
        log.info(f"Processing {len(bug_ids)} bugs for {project}")

        if max_bugs_per_project > 0:
            bug_ids = bug_ids[:max_bugs_per_project]
            log.info(f"Limited to {len(bug_ids)} bugs for {project} (max: {max_bugs_per_project})")

        if not bug_ids:
            log.warning(f"No bugs found for {project}")
            return []

        return classify_bugs_batch(project, bug_ids, workers)

    # Process projects in parallel
    with ThreadPoolExecutor(max_workers=min(workers, len(projects))) as executor:
        futures = [executor.submit(classify_project_bugs, project) for project in projects]

        for future in as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                log.error(f"Error processing project: {e}")

    # Sort results by project and bug_id
    all_results.sort(key=lambda x: (x.get("project", ""), int(x.get("bug_id", 0))))
    return all_results


def format_single_bug_output(bug_info: Dict[str, Any]) -> str:
    """Format single bug classification for text output.

    Args:
        bug_info: Bug classification information

    Returns:
        Formatted text output
    """
    output_lines = [
        f"Bug: {bug_info['project']}-{bug_info['bug_id']}",
        f"Type: {bug_info['type']}",
        f"Bug Report: {bug_info.get('bug_report_id', 'N/A')}",
        f"Revision: {bug_info.get('revision_id', 'N/A')}",
        ""
    ]

    if bug_info['root_causes']:
        output_lines.append("Root Causes:")
        for i, root_cause in enumerate(bug_info['root_causes'], 1):
            output_lines.append(f"  {i}. Test: {root_cause['test']}")
            output_lines.append(f"     Error: {root_cause['error']}")
        output_lines.append("")

    if bug_info['modified_sources']:
        output_lines.append("Modified Sources:")
        for source in bug_info['modified_sources']:
            output_lines.append(f"  - {source}")

    return "\n".join(output_lines)


def filter_functional_bugs(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter functional bugs from classification results.

    Args:
        results: List of classification results

    Returns:
        List of functional bugs
    """
    return [r for r in results if r.get("type") == "functional"]


def filter_nl2postcond_bugs(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter nl2postcond bugs from classification results.

    Args:
        results: List of classification results

    Returns:
        List of bugs that are in nl2postcond dataset
    """
    return [r for r in results if r.get("in_nl2postcond", False)]


def check_dump_status(dumps_base_dir: str, project_id: str, bug_id: str) -> Dict[str, Any]:
    """Check dump collection status for a specific bug.
    
    Args:
        dumps_base_dir: Base directory containing collected dumps
        project_id: Project identifier
        bug_id: Bug identifier (as string)
        
    Returns:
        Dictionary with status information
    """
    bug_dir = os.path.join(dumps_base_dir, project_id, bug_id)
    
    if not os.path.exists(bug_dir):
        return {
            "project": project_id,
            "bug_id": bug_id,
            "status": "not_found",
            "wrong_dumps": 0,
            "correct_dumps": 0,
            "total_dumps": 0
        }
    
    # Check wrong/ directory (failed test dumps)
    wrong_dir = os.path.join(bug_dir, "wrong")
    wrong_count = 0
    if os.path.exists(wrong_dir):
        wrong_count = len([f for f in os.listdir(wrong_dir) if f.endswith('.json')])
    
    # Check correct/ directory (passed test dumps)
    correct_dir = os.path.join(bug_dir, "correct")
    correct_count = 0
    if os.path.exists(correct_dir):
        correct_count = len([f for f in os.listdir(correct_dir) if f.endswith('.json')])
    
    total_count = wrong_count + correct_count
    
    # Success criteria: at least 1 failed dump (wrong/)
    if wrong_count > 0 and correct_count > 0:
        status = "success"
    elif correct_count > 0:
        status = "no_failed_dumps"
    elif wrong_count > 0:
        status = "no_correct_dumps"
    else:
        status = "no_dumps"
    
    return {
        "project": project_id,
        "bug_id": bug_id,
        "status": status,
        "wrong_dumps": wrong_count,
        "correct_dumps": correct_count,
        "total_dumps": total_count
    }


def scan_dumps_directory(dumps_base_dir: str, projects: List[str], valid_bugs: Dict[str, Set[int]] = None) -> List[Dict[str, Any]]:
    """Scan dumps directory and check status for all bugs.
    
    Args:
        dumps_base_dir: Base directory containing collected dumps
        projects: List of project names to scan
        valid_bugs: Optional dictionary of valid bugs to check (from defects4j_valids.csv)
                   If provided, checks only these bugs. Otherwise scans directory.
        
    Returns:
        List of status dictionaries for all found bugs
    """
    results = []
    nl2postcond_bugs = load_nl2postcond_bugs()
    
    if not os.path.exists(dumps_base_dir):
        log.warning(f"Dumps directory not found: {dumps_base_dir}")
    
    for project in projects:
        # If valid_bugs provided, use that list; otherwise scan directory
        if valid_bugs and project in valid_bugs:
            bug_ids = sorted([str(bug_id) for bug_id in valid_bugs[project]])
            log.info(f"Checking {len(bug_ids)} valid bugs for {project}")
        else:
            # Scan directory for bugs
            project_dir = os.path.join(dumps_base_dir, project)
            if not os.path.exists(project_dir):
                log.warning(f"Project directory not found: {project_dir}")
                continue
            
            try:
                bug_ids = sorted([d for d in os.listdir(project_dir) 
                                if os.path.isdir(os.path.join(project_dir, d))],
                               key=lambda x: int(x) if x.isdigit() else 0)
            except OSError as e:
                log.error(f"Error reading project directory {project_dir}: {e}")
                continue
            
            log.info(f"Found {len(bug_ids)} bugs for {project}")
        
        for bug_id in bug_ids:
            status = check_dump_status(dumps_base_dir, project, bug_id)
            # Add nl2postcond information
            nl2_set = nl2postcond_bugs.get(project, set())
            status["in_nl2postcond"] = bug_id in nl2_set
            results.append(status)
    
    return results


def write_dump_status_csv(file_path: str, results: List[Dict[str, Any]]) -> None:
    """Write dump status results to CSV file.
    
    Args:
        file_path: Path to output CSV file
        results: List of dump status results
    """
    if not results:
        log.warning("No results to write")
        return
    
    fieldnames = [
        "project", "bug_id", "status", "wrong_dumps", "correct_dumps", 
        "total_dumps", "in_nl2postcond"
    ]
    
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                "project": result.get("project", ""),
                "bug_id": result.get("bug_id", ""),
                "status": result.get("status", ""),
                "wrong_dumps": result.get("wrong_dumps", 0),
                "correct_dumps": result.get("correct_dumps", 0),
                "total_dumps": result.get("total_dumps", 0),
                "in_nl2postcond": result.get("in_nl2postcond", False)
            })


def write_dump_status_markdown(file_path: str, results: List[Dict[str, Any]]) -> None:
    """Write dump status results to markdown file.
    
    Args:
        file_path: Path to output markdown file
        results: List of dump status results
    """
    if not results:
        log.warning("No results to write")
        return
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("# Dump Collection Status Report\n\n")
        f.write(f"Total bugs scanned: {len(results)}\n\n")
        
        # Summary statistics
        success_count = sum(1 for r in results if r.get("status") == "success")
        no_failed_dumps_count = sum(1 for r in results if r.get("status") == "no_failed_dumps")
        no_dumps_count = sum(1 for r in results if r.get("status") == "no_dumps")
        not_found_count = sum(1 for r in results if r.get("status") == "not_found")
        nl2_count = sum(1 for r in results if r.get("in_nl2postcond", False))
        nl2_success_count = sum(1 for r in results if r.get("status") == "success" and r.get("in_nl2postcond", False))
        
        f.write("## Summary\n\n")
        f.write(f"- **Success** (≥1 failed dump): {success_count}\n")
        f.write(f"- **No failed dumps** (only correct dumps): {no_failed_dumps_count}\n")
        f.write(f"- **No dumps**: {no_dumps_count}\n")
        f.write(f"- **Not found**: {not_found_count}\n")
        f.write(f"- **NL2 Postcond bugs**: {nl2_count} ({nl2_success_count} successful)\n\n")
        
        # Table
        f.write("## Detailed Results\n\n")
        f.write("| Project | Bug ID | Status | Wrong Dumps | Correct Dumps | Total Dumps | NL2 |\n")
        f.write("|---------|--------|--------|-------------|---------------|-------------|-----|\n")
        
        for result in results:
            project = result.get("project", "")
            bug_id = result.get("bug_id", "")
            status = result.get("status", "")
            wrong_dumps = result.get("wrong_dumps", 0)
            correct_dumps = result.get("correct_dumps", 0)
            total_dumps = result.get("total_dumps", 0)
            nl2_indicator = "Yes" if result.get("in_nl2postcond", False) else "No"
            
            f.write(f"| {project} | {bug_id} | {status} | {wrong_dumps} | {correct_dumps} | {total_dumps} | {nl2_indicator} |\n")
        
        f.write("\n")
        
        # Status legend
        f.write("## Status Legend\n\n")
        f.write("- **success**: At least 1 failed test dump collected\n")
        f.write("- **no_failed_dumps**: Only passing test dumps collected (no failed dumps)\n")
        f.write("- **no_dumps**: Bug directory exists but no dumps found\n")
        f.write("- **not_found**: Bug directory does not exist\n")