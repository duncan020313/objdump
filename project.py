from typing import Dict, List, Optional, Set, Any
import os
import re
import logging
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")

from logging_setup import configure_logging
from jt_types import BuildSystem
import defects4j
from build_systems import detect, find_all_build_files
from build_systems.maven import setup_jackson_dependencies as setup_maven_jackson
from build_systems.ant import process_all_ant_files_in_dir as add_ant
from instrumentation.diff import compute_file_diff_ranges_both
from instrumentation.ts import extract_changed_methods
from instrumentation.instrumenter import instrument_changed_methods, copy_java_template_to_classdir
from instrumentation.test_extractor import extract_test_methods
from objdump_io.net import download_files
from collector import collect_dumps_safe
from concurrent.futures import ThreadPoolExecutor, as_completed

configure_logging()
log = logging.getLogger(__name__)

def download_jackson_jars(work_dir: str, version: str = "2.13.0") -> None:
    lib_dir = os.path.join(work_dir, "lib")
    items = [
        (f"jackson-core-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/{version}/jackson-core-{version}.jar"),
        (f"jackson-databind-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/{version}/jackson-databind-{version}.jar"),
        (f"jackson-annotations-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-annotations/{version}/jackson-annotations-{version}.jar"),
    ]
    download_files(lib_dir, items)

def extract_compilation_errors(work_dir: str) -> str:
    """Extract compilation errors from build output."""
    # Look for common error log files
    error_files = [
        os.path.join(work_dir, "build.log"),
        os.path.join(work_dir, "compile.log"),
        os.path.join(work_dir, "ant.log"),
        os.path.join(work_dir, "maven.log")
    ]
    
    for error_file in error_files:
        if os.path.isfile(error_file):
            try:
                with open(error_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Extract last 50 lines or first 1000 chars of errors
                    lines = content.split('\n')
                    if len(lines) > 50:
                        error_lines = lines[-50:]
                    else:
                        error_lines = lines
                    
                    error_text = '\n'.join(error_lines)
                    if len(error_text) > 1000:
                        error_text = error_text[:1000] + "..."
                    return error_text
            except Exception:
                continue
    
    return "No detailed error information available"


def detect_java_version(work_dir: str) -> str:
    """Detect Java version used in the project."""
    try:
        import subprocess
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stderr.split('\n')[0]
            return version_line.strip()
    except Exception:
        pass
    return "Unknown"


def checkout_versions(project_id: str, bug_id: str, work_dir: str) -> "tuple[str, str]":
    """Checkout buggy and fixed versions of the project.
    
    Returns:
        tuple: (buggy_dir, fixed_dir)
    """


    
    if os.path.exists(work_dir):
        log.info("Removing existing work dir: %s", work_dir)
        import shutil
        shutil.rmtree(work_dir)

    log.info("Checkout buggy version to %s", work_dir)
    if not defects4j.checkout(project_id, bug_id, work_dir, "b"):
        raise RuntimeError("checkout buggy failed")

    fixed_dir = f"{work_dir}_fixed"
    if os.path.exists(fixed_dir):
        import shutil
        shutil.rmtree(fixed_dir)
    log.info("Checkout fixed version to %s", fixed_dir)
    if not defects4j.checkout(project_id, bug_id, fixed_dir, "f"):
        raise RuntimeError("checkout fixed failed")
    
    return work_dir, fixed_dir


def setup_jackson_dependencies(work_dir: str, jackson_version: str = "2.13.0") -> None:
    """Setup Jackson dependencies for the project."""
    
    build_system = detect(work_dir)
    classes_dir = defects4j.get_source_classes_dir(work_dir)
    if build_system == BuildSystem.MAVEN:
        log.info("Detected Maven build system")
        setup_maven_jackson(work_dir, jackson_version)
    elif build_system == BuildSystem.ANT:
        log.info("Detected Ant build system")
        download_jackson_jars(work_dir, jackson_version)
        add_ant(work_dir, jackson_version, classes_dir)
    copy_java_template_to_classdir(work_dir, classes_dir)

def compile_project(work_dir: str) -> bool:
    """Compile the project and return success status."""
    
    
    # Ensure a default dump file exists for compile phase; actual dumps occur during test runs
    out_file = os.path.join(work_dir, "dump.json")
    env_vars = {"OBJDUMP_OUT": out_file}
    success, _, _ = defects4j.compile(work_dir, env=env_vars)
    return success


def instrument_changed_methods_step(work_dir: str, fixed_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """Instrument changed methods in the project."""
    
    
    modified_classes = (defects4j.export(work_dir, "classes.modified") or "").splitlines()
    modified_classes = [s for s in (c.strip() for c in modified_classes) if s]

    def to_path(class_path: str, modified: List[str]) -> List[str]:
        result: List[str] = []
        for mc in modified:
            cp = mc.replace(".", "/")
            result.append(os.path.join(class_path, cp))
        return result

    classes_dir = defects4j.get_source_classes_dir(work_dir)
    modified_class_paths = to_path(classes_dir, modified_classes) if classes_dir and modified_classes else []
    
    log.info(f"# of modified classes: {len(modified_class_paths)}")

    changed: Dict[str, List[str]] = {}
    # compute changes
    for buggy_cp in modified_class_paths:
        java_buggy = os.path.join(work_dir, buggy_cp + ".java")
        java_fixed = os.path.join(fixed_dir, buggy_cp + ".java")
        if not (os.path.isfile(java_buggy) and os.path.isfile(java_fixed)):
            continue
        ranges = compute_file_diff_ranges_both(java_buggy, java_fixed)

        changed[java_buggy] = sorted(set(extract_changed_methods(java_buggy, ranges["left"] + ranges["right"])))

    return instrument_changed_methods(changed)


def generate_instrumentation_report(instrumented_map: Dict[str, List[Dict[str, Any]]], work_dir: str, report_file: Optional[str] = None) -> None:
    """Generate instrumentation report."""
    
    
    report_items: List[Dict[str, Any]] = []
    for fpath, method_infos in instrumented_map.items():
        abs_path = os.path.abspath(fpath)
        for method_info in method_infos:
            report_items.append({
                "file": abs_path,
                "signature": method_info["signature"],
                "code": method_info["code"],
                "javadoc": method_info["javadoc"]
            })
    
    if report_file is None:
        report_file = os.path.join(work_dir, "instrumented_methods.json")
    
    payload = json.dumps(report_items, indent=2, ensure_ascii=False)
    
    grouped: Dict[str, List[str]] = {}
    for item in report_items:
        path = item["file"]
        sig = item["signature"]
        grouped.setdefault(path, []).append(sig)
    total = sum(len(v) for v in grouped.values())
    log.info(f"Instrumented methods ({total}):")
    for path in sorted(grouped.keys()):
        log.info(f"- {path}")
        for sig in grouped[path]:
            log.info(f"  - {sig}")

    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write(payload)


def filter_tests_by_directory_proximity(modified_classes: List[str], test_names: List[str]) -> List[str]:
    """Filter test names to only include those in the same package directory as modified source files.
    
    Args:
        modified_classes: List of modified source class names (e.g., ["org.apache.commons.math3.util.FastMath"])
        test_names: List of test class names (e.g., ["org.apache.commons.math3.util.ResizableDoubleArrayTest"])
        
    Returns:
        List of filtered test names that match package directories of modified classes
    """
    if not modified_classes or not test_names:
        return test_names
    
    # Extract package paths from modified classes
    modified_packages = set()
    for class_name in modified_classes:
        if '.' in class_name:
            package = class_name.rsplit('.', 1)[0]  # Remove class name, keep package
            modified_packages.add(package)
    
    if not modified_packages:
        return test_names
    
    # Filter test names by package matching
    filtered_tests = []
    for test_name in test_names:
        if '::' in test_name:
            # Extract class name from test method (e.g., "Class::method" -> "Class")
            class_name = test_name.split('::')[0]
        else:
            class_name = test_name
            
        if '.' in class_name:
            test_package = class_name.rsplit('.', 1)[0]  # Remove class name, keep package
            if test_package in modified_packages:
                filtered_tests.append(test_name)
        else:
            # If no package info, include the test (fallback)
            filtered_tests.append(test_name)
    
    return filtered_tests


def run_tests(work_dir: str) -> Dict[str, str]:
    """Run all relevant tests for the project and return their pass/fail status.
    
    Returns:
        Dictionary mapping test names to their status ("correct" for passing, "wrong" for failing)
    """
    # Prepare dumps directory for per-test outputs
    dumps_dir = os.path.join(work_dir, "dumps")
    os.makedirs(dumps_dir, exist_ok=True)

    out_file = os.path.join(work_dir, "dump.json")
    env_vars = {"OBJDUMP_OUT": out_file}
    
    defects4j.compile(work_dir, env=env_vars)
    
    # Get all relevant tests (includes trigger tests)
    relevant_tests = defects4j.export(work_dir, "tests.relevant")
    trigger_tests = defects4j.export(work_dir, "tests.trigger")
    
    assert relevant_tests is not None
    assert trigger_tests is not None
    
    # Get modified classes for filtering
    modified_classes_raw = defects4j.export(work_dir, "classes.modified")
    modified_classes = [s.strip() for s in modified_classes_raw.splitlines() if s.strip()] if modified_classes_raw else []
    
    test_results = {}
    
    # Filter relevant tests by directory proximity
    names_raw = [t.strip() for t in relevant_tests.splitlines() if t.strip()]
    log.info(f"Original relevant tests: {len(names_raw)}")
    
    if modified_classes:
        log.info(f"Modified classes: {modified_classes}")
        names = filter_tests_by_directory_proximity(modified_classes, names_raw)
        log.info(f"Filtered relevant tests: {len(names)}")
    else:
        names = names_raw
        log.info("No modified classes found, using all relevant tests")
    
    trigger_set = set()
    if trigger_tests:
        trigger_set = {t.strip() for t in trigger_tests.splitlines() if t.strip()}
        log.info(f"Trigger tests: {len(trigger_set)}")
    
    # Expand test classes into individual methods
    expanded_test_names = set(expand_test_classes(work_dir, names, log))
    
    def run_test(test_name: str, is_correct: bool) -> bool:
        safe = re.sub(r"[^A-Za-z0-9]", "-", test_name)
        dump_path = os.path.join(dumps_dir, f"{safe}.json")
        abs_dump_path = os.path.abspath(dump_path)
        per_test_env = {"OBJDUMP_OUT": abs_dump_path}
        
        # Run the test and check the result
        test_result = defects4j.test(work_dir, [test_name], env=per_test_env)
        
        # Handle different test results
        if test_result == "timeout":
            # Test timed out - skip it (don't add to test_results)
            log.warning(f"Test {test_name} timed out - skipping")
            return True  # Return True to indicate we handled it gracefully
        elif test_result is True:
            # Test passed
            test_results[test_name] = "correct" if is_correct else "wrong"
            return True
        else:
            # Test failed
            test_results[test_name] = "wrong"
            return True
    
    correct_tests = expanded_test_names - trigger_set
    
    log.info(f"Correct tests (after filtering): {len(correct_tests)}")
    log.info(f"Trigger tests: {len(trigger_set)}")
    log.info(f"Total tests to run: {len(expanded_test_names)}")
    
    def run_test_wrapper(args):
        test_name, is_correct = args
        return run_test(test_name, is_correct)
    
    # Prepare all test tasks
    test_tasks = []
    for test_name in correct_tests:
        test_tasks.append((test_name, True))
    for test_name in trigger_set:
        test_tasks.append((test_name, False))
    
    # Run tests in parallel
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(run_test_wrapper, task) for task in test_tasks]
        for future in as_completed(futures):
            future.result()  # Wait for completion and handle any exceptions
    return test_results


def expand_test_classes(work_dir: str, test_names: List[str], log) -> List[str]:
    """
    Expand test class names into individual test methods using multithreading.
    
    Args:
        work_dir: Working directory of the Defects4J project
        test_names: List of test names (may include classes or individual methods)
        log: Logger instance
        
    Returns:
        List of expanded test names (individual methods or original names if already methods)
    """
    def expand_single_test(test_name: str) -> List[str]:
        """Expand a single test class into individual test methods."""
        # Check if this is already a specific method (contains ::)
        if "::" in test_name:
            # Already a specific method, use as-is
            return [test_name]
        
        # This is a test class, try to expand it
        log.debug(f"Expanding test class: {test_name}")
        
        # Resolve test class to file path
        test_file_path = defects4j.resolve_test_class_path(work_dir, test_name)
        if not test_file_path:
            log.error(f"Could not resolve test class file for: {test_name}")
            # Fall back to running the entire class
            return [test_name]
        
        # Extract test methods from the class file
        test_methods = extract_test_methods(test_file_path)
        if not test_methods:
            log.error(f"Could not extract test methods from: {test_file_path}")
            # Fall back to running the entire class
            return [test_name]
        
        # Add each test method with class name prefix
        expanded_methods = []
        for method_name in test_methods:
            full_test_name = f"{test_name}::{method_name}"
            expanded_methods.append(full_test_name)
        
        log.debug(f"Expanded {test_name} into {len(test_methods)} methods")
        return expanded_methods
    
    # Use multithreading to expand test classes in parallel
    expanded_tests = []
    with ThreadPoolExecutor() as executor:
        # Submit all test expansion tasks
        futures = [executor.submit(expand_single_test, test_name) for test_name in test_names]
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                expanded_tests.extend(result)
            except Exception as e:
                log.error(f"Error expanding test class: {e}")
                # Add the original test name as fallback
                expanded_tests.append(test_names[futures.index(future)])
    
    return expanded_tests


def collect_dump_files(work_dir: str, project_id: str, bug_id: str, test_results: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Collect dump files after test execution."""
    
    
    # Use centralized location from environment variable or default
    output_base = os.environ.get("OBJDUMP_DUMPS_DIR", "/tmp/objdump_collected_dumps")
    collection_dir = collect_dumps_safe(work_dir, project_id, bug_id, output_base, test_results)
    if collection_dir:
        log.info(f"Collected dump files to: {collection_dir}")
    else:
        log.warning("Failed to collect dump files")
    
    return collection_dir


def run_all(project_id: str, bug_id: str, work_dir: str, jackson_version: str = "2.13.0", report_file: Optional[str] = None) -> None:
    """Run the complete workflow using step functions."""
    

    # Step 1: Checkout buggy and fixed versions
    buggy_dir, fixed_dir = checkout_versions(project_id, bug_id, work_dir)
    
    # Step 2: Setup Jackson dependencies
    setup_jackson_dependencies(work_dir, jackson_version)
    
    # Step 3: Compile project
    if not compile_project(work_dir):
        raise RuntimeError("Initial compilation failed")
    
    # Step 4: Instrument changed methods
    instrumented_map = instrument_changed_methods_step(work_dir, fixed_dir)
    
    # Step 5: Generate instrumentation report
    generate_instrumentation_report(instrumented_map, work_dir, report_file)
    
    # Check if any methods were instrumented
    total_instrumented = sum(len(method_infos) for method_infos in instrumented_map.values()) if instrumented_map else 0
    if total_instrumented == 0:
        log.info("No methods were instrumented, skipping test execution")
        return
    
    # Step 6: Run tests
    test_results = run_tests(work_dir)
    
    # Step 7: Collect dump files
    collect_dump_files(work_dir, project_id, bug_id, test_results)


def run_all_staged(project_id: str, bug_id: str, work_dir: str, jackson_version: str = "2.13.0", report_file: Optional[str] = None, skip_shared_build_injection: bool = False) -> Dict[str, Any]:
    """Run the full workflow with stage-wise status reporting using step functions.

    Returns a dictionary summarizing each stage outcome and any errors.
    """


    status: Dict[str, Any] = {
        "project": project_id,
        "bug_id": int(bug_id) if isinstance(bug_id, str) and bug_id.isdigit() else bug_id,
        "work_dir": work_dir,
        "stages": {
            "checkout": "pending",
            "jackson": "pending",
            "compile": "pending",
            "instrument": "pending",
            "rebuild": "pending",
            "tests": {"status": "pending", "triggering": [], "failures": None},
        },
        "error": None,
    }


    # Step 1: Checkout buggy and fixed versions
    _, fixed_dir = checkout_versions(project_id, bug_id, work_dir)
    status["stages"]["checkout"] = "ok"
    
    # Step 2: Setup Jackson dependencies
    setup_jackson_dependencies(work_dir, jackson_version)
    status["stages"]["jackson"] = "ok"
    
    # Step 3: Compile project
    if not compile_project(work_dir):
        status["stages"]["compile"] = "fail"
        status["error"] = "Initial compilation failed"
        return status
    status["stages"]["compile"] = {
        "status": "ok",
        "java_version": detect_java_version(work_dir)
    }

    # Step 4: Instrument changed methods
    instrumented_map = instrument_changed_methods_step(work_dir, fixed_dir)
    total_instrumented = sum(len(method_infos) for method_infos in instrumented_map.values()) if instrumented_map else 0
    status["stages"]["instrument"] = {
        "status": "ok",
        "methods_found": len([k for k, v in instrumented_map.items() if v]) if instrumented_map else 0,
        "methods_instrumented": total_instrumented
    }

    # Generate instrumentation report (best-effort)
    generate_instrumentation_report(instrumented_map, work_dir, report_file)

    # Check if any methods were instrumented
    if total_instrumented == 0:
        log.info("No methods were instrumented, skipping test execution")
        status["stages"]["tests"]["status"] = "skipped"
        status["stages"]["tests"]["reason"] = "No methods instrumented"
        status["stages"]["rebuild"] = "skipped"
        status["stages"]["collect_dumps"] = {"status": "skipped", "reason": "No methods instrumented"}
        return status

    # Step 5: Rebuild after instrumentation
    rebuild_success, rebuild_out, rebuild_err = defects4j.compile(work_dir, env={"OBJDUMP_OUT": os.path.join(work_dir, "dump.json")})
    if not rebuild_success:
        status["stages"]["rebuild"] = "fail"
        error_details = f"stdout: {rebuild_out}\nstderr: {rebuild_err}" if rebuild_out or rebuild_err else "No detailed error information available"
        status["error"] = f"rebuild failed: {error_details}"
        return status
    status["stages"]["rebuild"] = "ok"

    # Step 6: Run tests (all relevant tests)
    test_results = run_tests(work_dir)
    
    # Update status with test results
    correct_tests = [name for name, status in test_results.items() if status == "correct"]
    wrong_tests = [name for name, status in test_results.items() if status == "wrong"]
    
    status["stages"]["tests"]["status"] = "ok" if test_results else "fail"
    status["stages"]["tests"]["correct"] = correct_tests
    status["stages"]["tests"]["wrong"] = wrong_tests
    status["stages"]["tests"]["total"] = len(test_results)
    
    # Store test results for collection phase
    status["test_results"] = test_results

    # Step 7: Collect dump files after test execution
    try:
        # Use centralized location from environment variable or default
        output_base = os.environ.get("OBJDUMP_DUMPS_DIR", "/tmp/objdump_collected_dumps")
        collection_dir = collect_dumps_safe(work_dir, project_id, bug_id, output_base, test_results)
        if collection_dir:
            status["stages"]["collect_dumps"] = {"status": "ok", "collection_dir": collection_dir}
        else:
            status["stages"]["collect_dumps"] = {"status": "fail", "error": "Collection failed"}
    except Exception as e:
        status["stages"]["collect_dumps"] = {"status": "fail", "error": str(e)}

    return status

