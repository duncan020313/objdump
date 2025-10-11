#!/usr/bin/env python3
"""
Test script to verify if projects fail without Jackson dependency installation.
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path to import objdump modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project import run_all_staged
from build_systems import detect, find_all_build_files
from build_systems.maven import add_dependencies as add_maven, add_dependencies_to_maven_build_xml
from build_systems.ant import add_dependencies as add_ant
import defects4j


def run_without_jackson_install(project_id: str, bug_id: str, work_dir: str) -> dict:
    """Run the workflow without Jackson dependency installation."""
    
    # Clean work dirs if exist
    if os.path.exists(work_dir):
        import shutil
        shutil.rmtree(work_dir)
    fixed_dir = f"{work_dir}_fixed"
    if os.path.exists(fixed_dir):
        import shutil
        shutil.rmtree(fixed_dir)

    status = {
        "project": project_id,
        "bug_id": bug_id,
        "work_dir": work_dir,
        "stages": {
            "checkout": "pending",
            "jackson": "skipped",  # Skip Jackson installation
            "compile": "pending",
            "instrument": "pending",
            "rebuild": "pending",
            "tests": {"status": "pending", "triggering": [], "failures": None}
        },
        "error": None,
    }

    try:
        # Checkout buggy and fixed
        if not defects4j.checkout(project_id, bug_id, work_dir, "b"):
            status["stages"]["checkout"] = "fail"
            status["error"] = "checkout buggy failed"
            return status
        if not defects4j.checkout(project_id, bug_id, fixed_dir, "f"):
            status["stages"]["checkout"] = "fail"
            status["error"] = "checkout fixed failed"
            return status
        status["stages"]["checkout"] = "ok"

        # SKIP Jackson dependency installation
        print(f"  Skipping Jackson dependency installation for {project_id}-{bug_id}")

        # Initial compile (without Jackson)
        out_file = os.path.join(work_dir, "dump.jsonl")
        env_vars = {"OBJDUMP_OUT": out_file}
        compile_success, compile_out, compile_err = defects4j.compile(work_dir, env=env_vars)
        if not compile_success:
            status["stages"]["compile"] = "fail"
            error_details = f"stdout: {compile_out}\nstderr: {compile_err}" if compile_out or compile_err else "No detailed error information available"
            status["error"] = f"compile failed: {error_details}"
            return status
        status["stages"]["compile"] = {"status": "ok"}

        # Skip instrumentation and other stages for this test
        status["stages"]["instrument"] = "skipped"
        status["stages"]["rebuild"] = "skipped"
        status["stages"]["tests"] = {"status": "skipped", "triggering": [], "failures": None}

    except Exception as e:
        status["error"] = f"workflow failed: {e}"
        return status

    return status


def main():
    """Test JacksonCore and JacksonDatabind without Jackson installation."""
    
    test_projects = [
        {"project": "JacksonCore", "bug_id": "3"},
        {"project": "JacksonDatabind", "bug_id": "111"},
    ]
    
    print("=== Testing Projects WITHOUT Jackson Dependency Installation ===")
    print()
    
    results = []
    
    for project_info in test_projects:
        project = project_info["project"]
        bug_id = project_info["bug_id"]
        
        print(f"Testing {project}-{bug_id} WITHOUT Jackson installation...")
        
        work_dir = f"/tmp/objdump-test-no-jackson-{project.lower()}-{bug_id}"
        
        try:
            result = run_without_jackson_install(project, bug_id, work_dir)
            result['test_timestamp'] = datetime.utcnow().isoformat()
            results.append(result)
            
            # Print status
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
                elif stage_status == 'skipped':
                    status_summary.append('⏭️')
                else:
                    status_summary.append('–')
            
            print(f"  Status: {' '.join(status_summary)}")
            
            if result.get('error'):
                print(f"  Error: {result['error']}")
            
        except Exception as e:
            print(f"  Exception: {e}")
        
        print()
    
    # Print summary
    print("=== Summary ===")
    for result in results:
        project = result['project']
        bug_id = result['bug_id']
        compile_status = result['stages']['compile']
        if isinstance(compile_status, dict):
            compile_status = compile_status.get('status', 'pending')
        
        print(f"{project}-{bug_id}: Compile = {compile_status}")
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = f"/tmp/test_without_jackson_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
