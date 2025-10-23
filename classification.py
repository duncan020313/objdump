"""Bug classification module for Defects4J projects.

This module provides functionality to classify bugs as functional or exceptional
based on their root cause error types.
"""

from typing import List, Dict, Any
import csv
import defects4j
import logging
log = logging.getLogger(__name__)

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
                results.append(result)
            except Exception as e:
                results.append({
                    "project": project_id,
                    "bug_id": "?",
                    "type": "error",
                    "error": str(e)
                })

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
        "modified_sources_count", "root_causes", "modified_sources", "error"
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

        f.write("## Summary\n\n")
        f.write(f"- **Functional bugs**: {functional_count}\n")
        f.write(f"- **Exceptional bugs**: {exceptional_count}\n")
        f.write(f"- **Errors**: {error_count}\n\n")

        # Write table
        f.write("## Classification Results\n\n")
        f.write("| Project | Bug ID | Type | Bug Report | Root Causes | Modified Sources |\n")
        f.write("|---------|--------|------|------------|-------------|------------------|\n")

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

            f.write(f"| {project} | {bug_id} | {bug_type} | {bug_report} | {root_causes_str} | {modified_sources_str} |\n")

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