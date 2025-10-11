#!/usr/bin/env python3
"""
Test validation script for objdump on Defects4J bugs.

This script reads bugs from defects4j_valids.csv, selects a sample for testing,
and runs objdump on each bug sequentially to validate the tool's functionality.
"""

import csv
import os
import sys
import random
from typing import List, Dict, Any
from datetime import datetime

# Add the current directory to Python path to import objdump modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project import run_all_staged
from reports import write_jsonl, write_markdown_table, write_summary_statistics, write_detailed_errors


def read_bugs_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """Read bugs from defects4j_valids.csv file."""
    bugs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bugs.append(row)
    return bugs


def select_test_bugs(bugs: List[Dict[str, str]], target_count: int = 25) -> List[Dict[str, str]]:
    """Select a diverse sample of bugs for testing."""
    # Group bugs by project
    project_bugs = {}
    for bug in bugs:
        project = bug['project']
        if project not in project_bugs:
            project_bugs[project] = []
        project_bugs[project].append(bug)
    
    # Select bugs from each project proportionally
    selected = []
    projects = list(project_bugs.keys())
    
    # Calculate bugs per project (roughly equal distribution)
    bugs_per_project = max(1, target_count // len(projects))
    remaining_bugs = target_count
    
    for project in projects:
        project_bug_list = project_bugs[project]
        if remaining_bugs <= 0:
            break
            
        # Take up to bugs_per_project from this project
        take_count = min(bugs_per_project, len(project_bug_list), remaining_bugs)
        
        # Randomly sample from this project's bugs
        if take_count < len(project_bug_list):
            selected_from_project = random.sample(project_bug_list, take_count)
        else:
            selected_from_project = project_bug_list
            
        selected.extend(selected_from_project)
        remaining_bugs -= take_count
    
    # If we still need more bugs, fill from remaining
    if remaining_bugs > 0:
        all_remaining = []
        for project in projects:
            project_bug_list = project_bugs[project]
            already_selected = {f"{b['project']}-{b['bug_id']}" for b in selected}
            remaining = [b for b in project_bug_list if f"{b['project']}-{b['bug_id']}" not in already_selected]
            all_remaining.extend(remaining)
        
        if all_remaining:
            additional = random.sample(all_remaining, min(remaining_bugs, len(all_remaining)))
            selected.extend(additional)
    
    return selected


def run_validation_tests(selected_bugs: List[Dict[str, str]], work_base: str = "/tmp/objdump-validation") -> List[Dict[str, Any]]:
    """Run objdump validation tests on selected bugs."""
    results = []
    
    print(f"Starting validation tests on {len(selected_bugs)} bugs...")
    print(f"Work directory: {work_base}")
    print()
    
    for i, bug in enumerate(selected_bugs, 1):
        project = bug['project']
        bug_id = bug['bug_id']
        
        print(f"[{i}/{len(selected_bugs)}] Testing {project}-{bug_id}...")
        
        # Create work directory for this bug
        work_dir = os.path.join(work_base, f"{project.lower()}-{bug_id}")
        
        try:
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
            result['csv_data'] = bug
            
            results.append(result)
            
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
            
            print(f"  Status: {' '.join(status_summary)}")
            
            if result.get('error'):
                print(f"  Error: {result['error']}")
            
        except Exception as e:
            print(f"  Exception: {e}")
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
                'csv_data': bug
            }
            results.append(error_result)
        
        print()
    
    return results


def main():
    """Main function to run validation tests."""
    # Set random seed for reproducible results
    random.seed(42)
    
    # Configuration
    csv_path = "defects4j_valids.csv"
    work_base = "/tmp/objdump-validation"
    reports_dir = "reports"
    target_bug_count = 25
    
    print("=== objdump Validation Test ===")
    print(f"CSV file: {csv_path}")
    print(f"Target bugs: {target_bug_count}")
    print(f"Work directory: {work_base}")
    print(f"Reports directory: {reports_dir}")
    print()
    
    # Read bugs from CSV
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    print("Reading bugs from CSV...")
    all_bugs = read_bugs_from_csv(csv_path)
    print(f"Found {len(all_bugs)} bugs in CSV")
    
    # Select test bugs
    print("Selecting test bugs...")
    selected_bugs = select_test_bugs(all_bugs, target_bug_count)
    print(f"Selected {len(selected_bugs)} bugs for testing")
    
    # Show selected bugs
    print("\nSelected bugs:")
    for bug in selected_bugs:
        print(f"  - {bug['project']}-{bug['bug_id']}")
    print()
    
    # Run validation tests
    results = run_validation_tests(selected_bugs, work_base)
    
    # Generate reports
    print("Generating reports...")
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = f"validation_{timestamp}"
    
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
    
    for result in results:
        stages = result.get('stages', {})
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
    
    success_rate = (successful_bugs / total_bugs) * 100 if total_bugs > 0 else 0
    
    print(f"\n=== Final Summary ===")
    print(f"Total bugs tested: {total_bugs}")
    print(f"Successful bugs: {successful_bugs}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if successful_bugs < total_bugs:
        print(f"Failed bugs: {total_bugs - successful_bugs}")
        print("Check the error report for details.")


if __name__ == "__main__":
    main()
