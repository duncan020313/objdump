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
from build_systems import detect, find_all_build_files, inject_jackson_into_all_build_files, inject_jackson_into_defects4j_shared_build
from build_systems.maven import add_dependencies as add_maven
from build_systems.ant import add_dependencies as add_ant
from instrumentation.diff import compute_file_diff_ranges_both
from instrumentation.ts import extract_changed_methods
from instrumentation.instrumenter import instrument_changed_methods, copy_java_template_to_classdir
from tree_sitter import Parser
from tree_sitter_languages import get_language
from objdump_io.net import download_files
from collector import collect_dumps_safe


def download_jackson_jars(work_dir: str, version: str = "2.13.0") -> None:
    lib_dir = os.path.join(work_dir, "lib")
    items = [
        (f"jackson-core-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/{version}/jackson-core-{version}.jar"),
        (f"jackson-databind-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/{version}/jackson-databind-{version}.jar"),
        (f"jackson-annotations-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-annotations/{version}/jackson-annotations-{version}.jar"),
    ]
    download_files(lib_dir, items)


def validate_jackson_classpath(work_dir: str, jackson_version: str = "2.13.0") -> bool:
    """Verify Jackson jars are in project classpath and accessible."""
    lib_dir = os.path.join(work_dir, "lib")
    required_jars = [
        f"jackson-core-{jackson_version}.jar",
        f"jackson-databind-{jackson_version}.jar", 
        f"jackson-annotations-{jackson_version}.jar"
    ]
    
    # Check if jars exist
    for jar in required_jars:
        jar_path = os.path.join(lib_dir, jar)
        if not os.path.isfile(jar_path):
            print(f"Missing JAR: {jar_path}")
            return False
    
    # Check if jars are referenced in build files
    # Find all build files that might contain Jackson references
    all_build_files = find_all_build_files(work_dir)
    
    # Check each build file for Jackson references
    for build_file in all_build_files:
        if os.path.isfile(build_file):
            try:
                with open(build_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # For Maven POM files, check for jackson in dependencies
                    if build_file.endswith('pom.xml'):
                        if "jackson" not in content.lower():
                            print(f"Missing Jackson in POM: {build_file}")
                            return False
                    # For Ant build files (including maven-build.xml), check for jar references
                    elif build_file.endswith('.xml'):
                        # Check if any of the required jars are referenced
                        jar_found = False
                        for jar in required_jars:
                            if jar in content:
                                jar_found = True
                                break
                        if not jar_found:
                            print(f"Missing Jackson JARs in build file: {build_file}")
                            return False
            except (IOError, UnicodeDecodeError):
                # If we can't read the file, skip it but don't fail validation
                print(f"Warning: Could not read build file: {build_file}")
                continue
    
    # Special check for defects4j.build.xml which is critical
    defects4j_build = os.path.join(work_dir, "defects4j.build.xml")
    if os.path.isfile(defects4j_build):
        try:
            with open(defects4j_build, 'r', encoding='utf-8') as f:
                content = f.read()
                jar_found = False
                for jar in required_jars:
                    if jar in content:
                        jar_found = True
                        break
                if not jar_found:
                    print(f"Missing Jackson JARs in defects4j.build.xml: {defects4j_build}")
                    return False
        except (IOError, UnicodeDecodeError):
            print(f"Warning: Could not read defects4j.build.xml: {defects4j_build}")
    
    return True


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


def fix_math_build_xml_override(work_dir: str, jackson_version: str = "2.13.0") -> None:
    """Fix the Math.build.xml override that removes Jackson dependencies."""
    import xml.etree.ElementTree as ET
    
    # The Math.build.xml is in the Defects4J framework, but we can create a local override
    # by modifying the project's build.xml to include Jackson dependencies in a way that
    # won't be overridden by Math.build.xml
    
    build_xml_path = os.path.join(work_dir, "build.xml")
    if not os.path.isfile(build_xml_path):
        return
    
    try:
        tree = ET.parse(build_xml_path)
        root = tree.getroot()
        
        # Find the build.classpath and ensure Jackson dependencies are included
        for path_tag in root.findall('path'):
            if path_tag.get('id') == 'build.classpath':
                # Check if Jackson dependencies are already present
                existing_locations = {pe.get('location') for pe in path_tag.findall('pathelement')}
                
                jackson_deps = [
                    f"lib/jackson-core-{jackson_version}.jar",
                    f"lib/jackson-databind-{jackson_version}.jar", 
                    f"lib/jackson-annotations-{jackson_version}.jar"
                ]
                
                for dep in jackson_deps:
                    if dep not in existing_locations:
                        ET.SubElement(path_tag, 'pathelement', {'location': dep})
                
                break
        
        # Also ensure compile.classpath includes Jackson dependencies
        for path_tag in root.findall('path'):
            if path_tag.get('id') == 'compile.classpath':
                # Check if it references build.classpath
                for ref_tag in path_tag.findall('path'):
                    if ref_tag.get('refid') == 'build.classpath':
                        # Add Jackson dependencies directly to compile.classpath as well
                        existing_locations = {pe.get('location') for pe in path_tag.findall('pathelement')}
                        
                        for dep in jackson_deps:
                            if dep not in existing_locations:
                                ET.SubElement(path_tag, 'pathelement', {'location': dep})
                        break
                break
        
        tree.write(build_xml_path, encoding='utf-8', xml_declaration=True)
        
    except Exception as e:
        print(f"Warning: Failed to fix Math build.xml override: {e}")


def checkout_versions(project_id: str, bug_id: str, work_dir: str) -> "tuple[str, str]":
    """Checkout buggy and fixed versions of the project.
    
    Returns:
        tuple: (buggy_dir, fixed_dir)
    """
    configure_logging()
    log = logging.getLogger("jackson_installer")

    
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


def setup_jackson_dependencies(work_dir: str, jackson_version: str = "2.13.0", skip_shared_build_injection: bool = False, project_id: Optional[str] = None) -> None:
    """Setup Jackson dependencies for the project."""
    configure_logging()
    log = logging.getLogger("jackson_installer")
    
    # Inject Jackson into project template build files first
    if project_id:
        log.info(f"Injecting Jackson into project template for {project_id}")
        from build_systems import inject_jackson_into_project_templates
        inject_jackson_into_project_templates([project_id], jackson_version)
    else:
        log.info("No project ID provided, skipping project template injection")
    
    build_system = detect(work_dir)
    if build_system == BuildSystem.MAVEN:
        log.info("Detected Maven build system")
        pom_path = os.path.join(work_dir, "pom.xml")
        add_maven(pom_path, jackson_version)
    elif build_system == BuildSystem.ANT:
        log.info("Detected Ant build system")
    else:
        log.info("Unknown build system, trying Ant-style injection")
    
    # Fix encoding and nowarn attributes in individual build files
    classes_dir = defects4j.get_source_classes_dir(work_dir)
    build_xml = os.path.join(work_dir, "build.xml")
    if os.path.isfile(build_xml):
        add_ant(build_xml, jackson_version, classes_dir)
    
    # Inject Jackson into Defects4J shared build files (centralized approach)
    # Skip this if already done at the matrix level for efficiency
    if not skip_shared_build_injection:
        log.info("Injecting Jackson into Defects4J shared build files")
        inject_jackson_into_defects4j_shared_build(jackson_version)
    else:
        log.info("Skipping shared build injection (already done at matrix level)")

    # Always ensure JARs present under lib/ for Ant-driven builds
    log.info("Downloading Jackson JAR files")
    download_jackson_jars(work_dir, jackson_version)
    
    copy_java_template_to_classdir(work_dir, classes_dir)


def compile_project(work_dir: str) -> bool:
    """Compile the project and return success status."""
    configure_logging()
    log = logging.getLogger("jackson_installer")
    
    # Ensure a default dump file exists for compile phase; actual dumps occur during test runs
    out_file = os.path.join(work_dir, "dump.jsonl")
    env_vars = {"OBJDUMP_OUT": out_file}
    success, _, _ = defects4j.compile(work_dir, env=env_vars)
    return success


def instrument_changed_methods_step(work_dir: str, fixed_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """Instrument changed methods in the project."""
    configure_logging()
    log = logging.getLogger("jackson_installer")
    
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
    print(f"Instrumented methods ({total}):")
    for path in sorted(grouped.keys()):
        print(f"- {path}")
        for sig in grouped[path]:
            print(f"  - {sig}")

    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write(payload)


def run_tests(work_dir: str) -> None:
    """Run tests for the project."""
    configure_logging()
    log = logging.getLogger("jackson_installer")
    
    # Prepare dumps directory for per-test outputs
    dumps_dir = os.path.join(work_dir, "dumps")
    os.makedirs(dumps_dir, exist_ok=True)

    out_file = os.path.join(work_dir, "dump.jsonl")
    env_vars = {"OBJDUMP_OUT": out_file}
    
    defects4j.compile(work_dir, env=env_vars)
    tests = defects4j.export(work_dir, "tests.trigger")
    if tests:
        names = [t.strip() for t in tests.splitlines() if t.strip()]
        # Print triggering test list for visibility
        print(f"Triggering tests ({len(names)}):")
        for name in names:
            print(f"- {name}")
            safe = re.sub(r"[^A-Za-z0-9]", "-", name)
            dump_path = os.path.join(dumps_dir, f"{safe}.jsonl")
            abs_dump_path = os.path.abspath(dump_path)
            print(f"Running test {name} with dump path {abs_dump_path}")
            per_test_env = {"OBJDUMP_OUT": abs_dump_path}
            defects4j.test(work_dir, [name], env=per_test_env)
    else:
        # Fall back to running the full test suite if no triggering tests are exported
        print("No triggering tests exported; running full test suite.")
        defects4j.test(work_dir, env=env_vars)


def collect_dump_files(work_dir: str, project_id: str, bug_id: str) -> Optional[str]:
    """Collect dump files after test execution."""
    configure_logging()
    log = logging.getLogger("jackson_installer")
    
    # Use centralized location from environment variable or default
    output_base = os.environ.get("OBJDUMP_DUMPS_DIR", "/tmp/objdump_collected_dumps")
    collection_dir = collect_dumps_safe(work_dir, project_id, bug_id, output_base)
    if collection_dir:
        print(f"Collected dump files to: {collection_dir}")
    else:
        print("Warning: Failed to collect dump files")
    
    return collection_dir


def run_all(project_id: str, bug_id: str, work_dir: str, jackson_version: str = "2.13.0", report_file: Optional[str] = None) -> None:
    """Run the complete workflow using step functions."""
    configure_logging()
    log = logging.getLogger("jackson_installer")

    # Step 1: Checkout buggy and fixed versions
    buggy_dir, fixed_dir = checkout_versions(project_id, bug_id, work_dir)
    
    # Step 2: Setup Jackson dependencies
    setup_jackson_dependencies(work_dir, jackson_version, project_id=project_id)
    
    # Step 3: Compile project
    if not compile_project(work_dir):
        raise RuntimeError("Initial compilation failed")
    
    # Step 4: Instrument changed methods
    instrumented_map = instrument_changed_methods_step(work_dir, fixed_dir)
    
    # Step 5: Generate instrumentation report
    generate_instrumentation_report(instrumented_map, work_dir, report_file)
    
    # Step 6: Run tests
    run_tests(work_dir)
    
    # Step 7: Collect dump files
    collect_dump_files(work_dir, project_id, bug_id)


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
    setup_jackson_dependencies(work_dir, jackson_version, skip_shared_build_injection, project_id)
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
    
    # Post-compile Jackson re-injection for newly generated build files
    try:
        inject_jackson_into_all_build_files(work_dir, jackson_version)
        # Re-validate Jackson classpath after re-injection
        if not validate_jackson_classpath(work_dir, jackson_version):
            print("Warning: Jackson classpath validation failed after re-injection")
    except Exception as e:
        print(f"Warning: Post-compile Jackson re-injection failed: {e}")

    # Step 4: Instrument changed methods
    instrumented_map = instrument_changed_methods_step(work_dir, fixed_dir)
    status["stages"]["instrument"] = {
        "status": "ok",
        "methods_found": len([k for k, v in instrumented_map.items() if v]) if instrumented_map else 0,
        "methods_instrumented": sum(len(method_infos) for method_infos in instrumented_map.values()) if instrumented_map else 0
    }
    
    # Generate instrumentation report (best-effort)
    generate_instrumentation_report(instrumented_map, work_dir, report_file)

    # Step 5: Rebuild after instrumentation
    rebuild_success, rebuild_out, rebuild_err = defects4j.compile(work_dir, env={"OBJDUMP_OUT": os.path.join(work_dir, "dump.jsonl")})
    if not rebuild_success:
        status["stages"]["rebuild"] = "fail"
        error_details = f"stdout: {rebuild_out}\nstderr: {rebuild_err}" if rebuild_out or rebuild_err else "No detailed error information available"
        status["error"] = f"rebuild failed: {error_details}"
        return status
    status["stages"]["rebuild"] = "ok"

    # Step 6: Run tests (triggering if available)
    dumps_dir = os.path.join(work_dir, "dumps")
    try:
        os.makedirs(dumps_dir, exist_ok=True)
    except Exception:
        pass

    tests = defects4j.export(work_dir, "tests.trigger")
    if tests:
        names = [t.strip() for t in tests.splitlines() if t.strip()]
        status["stages"]["tests"]["triggering"] = names
        all_ok = True
        for name in names:
            safe = re.sub(r"[^A-Za-z0-9]", "-", name)
            dump_path = os.path.join(dumps_dir, f"{safe}.jsonl")
            abs_dump_path = os.path.abspath(dump_path)
            if not defects4j.test(work_dir, [name], env={"OBJDUMP_OUT": abs_dump_path}):
                all_ok = False
        status["stages"]["tests"]["status"] = "ok" if all_ok else "fail"
    else:
        if defects4j.test(work_dir, env={"OBJDUMP_OUT": os.path.join(work_dir, "dump.jsonl")}):
            status["stages"]["tests"]["status"] = "ok"
        else:
            status["stages"]["tests"]["status"] = "fail"

    # Step 7: Collect dump files after test execution
    try:
        # Use centralized location from environment variable or default
        output_base = os.environ.get("OBJDUMP_DUMPS_DIR", "/tmp/objdump_collected_dumps")
        collection_dir = collect_dumps_safe(work_dir, project_id, bug_id, output_base)
        if collection_dir:
            status["stages"]["collect_dumps"] = {"status": "ok", "collection_dir": collection_dir}
        else:
            status["stages"]["collect_dumps"] = {"status": "fail", "error": "Collection failed"}
    except Exception as e:
        status["stages"]["collect_dumps"] = {"status": "fail", "error": str(e)}

    return status

