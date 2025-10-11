#!/usr/bin/env python3
"""
Test script for previously failed projects with parallel execution.

This script tests the projects that previously failed due to Jackson dependency issues,
using multiple workers for parallel execution.
"""

import os
import sys
import json
import time
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add the current directory to Python path to import objdump modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project import run_all_staged
from reports import write_jsonl, write_markdown_table, write_summary_statistics, write_detailed_errors


# Previously failed projects from the validation report
FAILED_PROJECTS = [
    {"project": "Chart", "bug_id": "21"},
    {"project": "Cli", "bug_id": "1"},
    {"project": "Cli", "bug_id": "3"},
    {"project": "Closure", "bug_id": "6"},
    {"project": "Codec", "bug_id": "15"},
    {"project": "Collections", "bug_id": "12"},
    {"project": "Compress", "bug_id": "11"},
    {"project": "Csv", "bug_id": "7"},
    {"project": "Gson", "bug_id": "8"},
    {"project": "JacksonCore", "bug_id": "3"},
    {"project": "JacksonDatabind", "bug_id": "111"},
    {"project": "JacksonXml", "bug_id": "1"},
    {"project": "Jsoup", "bug_id": "17"},
    {"project": "Jsoup", "bug_id": "30"},
    {"project": "Jsoup", "bug_id": "69"},
    {"project": "JxPath", "bug_id": "8"},
    {"project": "JxPath", "bug_id": "15"},
    {"project": "Lang", "bug_id": "29"},
    {"project": "Math", "bug_id": "9"},
    {"project": "Math", "bug_id": "36"},
    {"project": "Mockito", "bug_id": "13"},
    {"project": "Time", "bug_id": "4"},
]

# Thread-safe counter for progress tracking
progress_lock = threading.Lock()
completed_count = 0


def test_single_project(project_info: Dict[str, str], work_base: str = "/tmp/objdump-validation") -> Dict[str, Any]:
    """Test a single project and return the result."""
    global completed_count
    
    project = project_info["project"]
    bug_id = project_info["bug_id"]
    
    # Create work directory for this bug
    work_dir = os.path.join(work_base, f"{project.lower()}-{bug_id}")
    
    # Thread ID for logging
    thread_id = threading.current_thread().name
    
    try:
        with progress_lock:
            completed_count += 1
            current = completed_count
            total = len(FAILED_PROJECTS)
        
        print(f"[Worker {thread_id}] [{current}/{total}] Testing {project}-{bug_id}...")
        
        # Run the staged workflow
        result = run_all_staged(
            project_id=project,
            bug_id=bug_id,
            work_dir=work_dir,
            jackson_version="2.13.0",
            instrument_all_modified=True
        )
        
        # Add some metadata
        result['test_timestamp'] = datetime.utcnow().isoformat()
        result['csv_data'] = project_info
        result['worker_id'] = thread_id
        
        # Print brief status
        stages = result.get('stages', {})
        status_summary = []
        for stage in ['checkout', 'jackson', 'compile', 'instrument', 'rebuild', 'tests']:
            stage_status = stages.get(stage)
            if isinstance(stage_status, dict):
                stage_status = stage_status.get('status', 'pending')
            
            if stage_status == 'ok':
                status_summary.append('✅')
            elif stage_status == 'fail':
                status_summary.append('❌')
            else:
                status_summary.append('⏭️')
        
        print(f"[Worker {thread_id}] {project}-{bug_id} Status: {' '.join(status_summary)}")
        
        if result.get('error'):
            print(f"[Worker {thread_id}] {project}-{bug_id} Error: {result['error']}")
        
        return result
        
    except Exception as e:
        print(f"[Worker {thread_id}] {project}-{bug_id} Exception: {e}")
        # Create error result
        error_result = {
            'project': project,
            'bug_id': int(bug_id) if bug_id.isdigit() else bug_id,
            'work_dir': work_dir,
            'stages': {
                'checkout': 'fail',
                'jackson': 'pending',
                'compile': 'pending',
                'instrument': 'pending',
                'rebuild': 'pending',
                'tests': {'status': 'pending', 'triggering': [], 'failures': None}
            },
            'error': str(e),
            'test_timestamp': datetime.utcnow().isoformat(),
            'csv_data': project_info,
            'worker_id': thread_id
        }
        return error_result


def run_parallel_validation_tests(projects: List[Dict[str, str]], work_base: str = "/tmp/objdump-validation", max_workers: int = 4) -> List[Dict[str, Any]]:
    """Run validation tests on projects in parallel."""
    results = []
    
    print(f"Starting parallel validation tests on {len(projects)} projects...")
    print(f"Work directory: {work_base}")
    print(f"Max workers: {max_workers}")
    print()
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Worker") as executor:
        # Submit all tasks
        future_to_project = {
            executor.submit(test_single_project, project, work_base): project 
            for project in projects
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_project):
            project = future_to_project[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing {project['project']}-{project['bug_id']}: {e}")
                # Create error result
                error_result = {
                    'project': project['project'],
                    'bug_id': int(project['bug_id']) if project['bug_id'].isdigit() else project['bug_id'],
                    'work_dir': os.path.join(work_base, f"{project['project'].lower()}-{project['bug_id']}"),
                    'stages': {
                        'checkout': 'fail',
                        'jackson': 'pending',
                        'compile': 'pending',
                        'instrument': 'pending',
                        'rebuild': 'pending',
                        'tests': {'status': 'pending', 'triggering': [], 'failures': None}
                    },
                    'error': str(e),
                    'test_timestamp': datetime.utcnow().isoformat(),
                    'csv_data': project,
                    'worker_id': 'Error'
                }
                results.append(error_result)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nCompleted {len(results)} tests in {duration:.1f} seconds")
    print(f"Average time per test: {duration/len(results):.1f} seconds")
    
    return results


def main():
    """Main function to run parallel validation tests."""
    # Configuration
    work_base = "/tmp/objdump-validation"
    reports_dir = "reports"
    max_workers = 6  # Adjust based on system capabilities
    
    print("=== objdump Failed Projects Validation Test ===")
    print(f"Projects to test: {len(FAILED_PROJECTS)}")
    print(f"Max workers: {max_workers}")
    print(f"Work directory: {work_base}")
    print(f"Reports directory: {reports_dir}")
    print()
    
    # Show projects to be tested
    print("Projects to be tested:")
    for project in FAILED_PROJECTS:
        print(f"  - {project['project']}-{project['bug_id']}")
    print()
    
    # Run parallel validation tests
    results = run_parallel_validation_tests(FAILED_PROJECTS, work_base, max_workers)
    
    # Generate reports
    print("Generating reports...")
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = f"failed_projects_validation_{timestamp}"
    
    # Write reports
    jsonl_path = os.path.join(reports_dir, f"{base_name}.jsonl")
    md_path = os.path.join(reports_dir, f"{base_name}.md")
    summary_path = os.path.join(reports_dir, f"{base_name}_summary.md")
    errors_path = os.path.join(reports_dir, f"{base_name}_errors.md")
    
    write_jsonl(jsonl_path, results)
    write_markdown_table(md_path, results)
    write_summary_statistics(summary_path, results)
    write_detailed_errors(errors_path, results)
    
    print(f"\nReports generated:")
    print(f"  - {jsonl_path}")
    print(f"  - {md_path}")
    print(f"  - {summary_path}")
    print(f"  - {errors_path}")
    
    # Print summary
    total_bugs = len(results)
    successful_bugs = 0
    jackson_success = 0
    compile_success = 0
    
    for result in results:
        stages = result.get('stages', {})
        
        # Check Jackson stage specifically
        jackson_status = stages.get('jackson')
        if isinstance(jackson_status, dict):
            jackson_status = jackson_status.get('status', 'pending')
        if jackson_status == 'ok':
            jackson_success += 1
        
        # Check compile stage specifically
        compile_status = stages.get('compile')
        if isinstance(compile_status, dict):
            compile_status = compile_status.get('status', 'pending')
        if compile_status == 'ok':
            compile_success += 1
        
        # Check if all stages passed
        all_passed = True
        for stage in ['checkout', 'jackson', 'compile', 'instrument', 'rebuild', 'tests']:
            stage_status = stages.get(stage)
            if isinstance(stage_status, dict):
                stage_status = stage_status.get('status', 'pending')
            if stage_status not in ['ok', 'skipped']:
                all_passed = False
                break
        
        if all_passed:
            successful_bugs += 1
    
    jackson_rate = (jackson_success / total_bugs) * 100 if total_bugs > 0 else 0
    compile_rate = (compile_success / total_bugs) * 100 if total_bugs > 0 else 0
    success_rate = (successful_bugs / total_bugs) * 100 if total_bugs > 0 else 0
    
    print(f"\n=== Final Summary ===")
    print(f"Total projects tested: {total_bugs}")
    print(f"Jackson stage success: {jackson_success} ({jackson_rate:.1f}%)")
    print(f"Compile stage success: {compile_success} ({compile_rate:.1f}%)")
    print(f"Overall success: {successful_bugs} ({success_rate:.1f}%)")
    
    if successful_bugs < total_bugs:
        print(f"Failed projects: {total_bugs - successful_bugs}")
        print("Check the error report for details.")


if __name__ == "__main__":
    main()
