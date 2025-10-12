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
from build_systems import detect, find_all_build_files, fix_encoding_in_build_files, inject_jackson_into_all_build_files
from build_systems.maven import add_dependencies as add_maven, add_dependencies_to_maven_build_xml
from build_systems.ant import add_dependencies as add_ant
from instrumentation.diff import compute_file_diff_ranges_both
from instrumentation.ts import extract_changed_methods
from instrumentation.instrumenter import instrument_changed_methods
from instrumentation.helpers import ensure_helper_sources
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


def run_all(project_id: str, bug_id: str, work_dir: str, jackson_version: str = "2.13.0", instrument_all_modified: bool = False, report_file: Optional[str] = None) -> None:
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

    build_system = detect(work_dir)
    if build_system == BuildSystem.MAVEN:
        log.info("Detected Maven build system")
        pom_path = os.path.join(work_dir, "pom.xml")
        add_maven(pom_path, jackson_version)
    elif build_system == BuildSystem.ANT:
        log.info("Detected Ant build system")
    else:
        log.info("Unknown build system, trying Ant-style injection")
    
    # Defects4J uses Ant under the hood; ensure Ant build has Jackson jars regardless
    build_xml = os.path.join(work_dir, "build.xml")
    if os.path.isfile(build_xml):
        add_ant(build_xml, jackson_version)
    
    # Find and modify all other build files that might need Jackson dependencies
    inject_jackson_into_all_build_files(work_dir, jackson_version)

    # Always ensure JARs present under lib/ for Ant-driven builds
    log.info("Downloading Jackson JAR files")
    download_jackson_jars(work_dir, jackson_version)

    # Get source directory for helper sources
    classes_dir = defects4j.export(work_dir, "dir.src.classes") or ""
    
    # Ensure helper sources are available
    log.info("Ensuring helper sources")
    ensure_helper_sources(work_dir, classes_dir or "src/main/java")

    # Ensure a default dump file exists for compile phase; actual dumps occur during test runs
    out_file = os.path.join(work_dir, "dump.jsonl")
    env_vars = {"OBJDUMP_OUT": out_file}
    defects4j.compile(work_dir, env=env_vars)
    modified_classes = (defects4j.export(work_dir, "classes.modified") or "").splitlines()
    modified_classes = [s for s in (c.strip() for c in modified_classes) if s]

    def to_path(class_path: str, modified: List[str]) -> List[str]:
        result: List[str] = []
        for mc in modified:
            cp = mc.replace(".", "/")
            result.append(os.path.join(class_path, cp))
        return result

    modified_class_paths = to_path(classes_dir, modified_classes) if classes_dir and modified_classes else []

    changed: Dict[str, List[str]] = {}
    # compute changes
    for buggy_cp in modified_class_paths:
        java_buggy = os.path.join(work_dir, buggy_cp + ".java")
        java_fixed = os.path.join(fixed_dir, buggy_cp + ".java")
        if not (os.path.isfile(java_buggy) and os.path.isfile(java_fixed)):
            continue
        ranges = compute_file_diff_ranges_both(java_buggy, java_fixed)
        methods = set()
        if ranges.get("left"):
            methods.update(extract_changed_methods(java_buggy, ranges["left"]))
        if ranges.get("right"):
            methods.update(extract_changed_methods(java_fixed, ranges["right"]))
        if methods:
            changed[java_buggy] = sorted(methods)

    src_java_rel = defects4j.export(work_dir, "dir.src.java") or "src/main/java"
    ensure_helper_sources(work_dir, src_java_rel)
    download_jackson_jars(work_dir, jackson_version)

    instrumented_map: Dict[str, List[str]] = {}
    if changed:
        instrumented_map = instrument_changed_methods(changed)
    else:
        if instrument_all_modified and modified_class_paths:
            # Collect all methods in modified files
            from tree_sitter import Parser
            from tree_sitter_languages import get_language
            all_map: Dict[str, List[str]] = {}
            for p in modified_class_paths:
                jf = os.path.join(work_dir, p + ".java")
                if not os.path.isfile(jf):
                    continue
                try:
                    lang = get_language("java")
                    parser = Parser()
                    parser.set_language(lang)
                    with open(jf, "rb") as f:
                        s = f.read()
                    t = parser.parse(s)
                    cursor = t.walk()
                    stack = [cursor.node]
                    sigs: Set[str] = set()
                    from instrumentation.ts import method_signature_from_node
                    while stack:
                        n = stack.pop()
                        if n.type in ("method_declaration", "constructor_declaration"):
                            sigs.add(method_signature_from_node(s, n))
                        for i in range(n.child_count):
                            stack.append(n.child(i))
                    if sigs:
                        all_map[jf] = sorted(sigs)
                except Exception:
                    continue
            if all_map:
                instrumented_map = instrument_changed_methods(all_map)

    # Emit instrumented method paths report (pretty stdout and JSON file)
    try:
        flat: List[str] = []
        for fpath, sigs in instrumented_map.items():
            abs_path = os.path.abspath(fpath)
            for sig in sigs:
                flat.append(f"{abs_path}::{sig}")
        if report_file is None:
            report_file = os.path.join(work_dir, "instrumented_methods.json")
        payload = json.dumps(sorted(flat))
        # Pretty stdout for humans; keep JSON in file for tools
        try:
            grouped: Dict[str, List[str]] = {}
            for item in sorted(flat):
                path, sig = item.split("::", 1)
                grouped.setdefault(path, []).append(sig)
            total = sum(len(v) for v in grouped.values())
            print(f"Fixed methods ({total}):")
            for path in sorted(grouped.keys()):
                print(f"- {path}")
                for sig in grouped[path]:
                    print(f"  - {sig}")
        except Exception:
            # Fallback to raw JSON on stdout if pretty printing fails
            print(payload)
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as rf:
            rf.write(payload)
    except Exception:
        # Do not fail the workflow on reporting errors
        pass

    # Prepare dumps directory for per-test outputs
    dumps_dir = os.path.join(work_dir, "dumps")
    try:
        os.makedirs(dumps_dir, exist_ok=True)
    except Exception:
        pass

    defects4j.compile(work_dir, env=env_vars)
    tests = defects4j.export(work_dir, "tests.trigger")
    if tests:
        names = [t.strip() for t in tests.splitlines() if t.strip()]
        # Print triggering test list for visibility
        try:
            print(f"Triggering tests ({len(names)}):")
            for name in names:
                print(f"- {name}")
        except Exception:
            pass
        for name in names:
            safe = re.sub(r"[^A-Za-z0-9]", "-", name)
            dump_path = os.path.join(dumps_dir, f"{safe}.jsonl")
            abs_dump_path = os.path.abspath(dump_path)
            print(f"Running test {name} with dump path {abs_dump_path}")
            per_test_env = {"OBJDUMP_OUT": abs_dump_path}
            defects4j.test(work_dir, [name], env=per_test_env)
    else:
        # Fall back to running the full test suite if no triggering tests are exported
        try:
            print("No triggering tests exported; running full test suite.")
        except Exception:
            pass
        defects4j.test(work_dir, env=env_vars)

    # Collect dump files after test execution
    try:
        # Use centralized location from environment variable or default
        output_base = os.environ.get("OBJDUMP_DUMPS_DIR", "/tmp/objdump_collected_dumps")
        collection_dir = collect_dumps_safe(work_dir, project_id, bug_id, output_base)
        if collection_dir:
            print(f"Collected dump files to: {collection_dir}")
        else:
            print("Warning: Failed to collect dump files")
    except Exception as e:
        print(f"Warning: Error during dump collection: {e}")


def run_all_staged(project_id: str, bug_id: str, work_dir: str, jackson_version: str = "2.13.0", instrument_all_modified: bool = False, report_file: Optional[str] = None) -> Dict[str, Any]:
    """Run the full workflow with stage-wise status reporting.

    Returns a dictionary summarizing each stage outcome and any errors.
    """
    configure_logging()
    log = logging.getLogger("jackson_installer")

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

    try:
        # Clean work dirs if exist
        if os.path.exists(work_dir):
            import shutil
            shutil.rmtree(work_dir)
        fixed_dir = f"{work_dir}_fixed"
        if os.path.exists(fixed_dir):
            import shutil
            shutil.rmtree(fixed_dir)

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

        # Detect build system and inject Jackson (POM/build.xml and JARs)
        try:
            build_system = detect(work_dir)
            if build_system == BuildSystem.MAVEN:
                pom_path = os.path.join(work_dir, "pom.xml")
                add_maven(pom_path, jackson_version)
                # Also check for maven-build.xml in Defects4J projects
                maven_build_xml = os.path.join(work_dir, "maven-build.xml")
                if os.path.isfile(maven_build_xml):
                    add_dependencies_to_maven_build_xml(maven_build_xml, jackson_version)
            
            # For ANT or unknown, try Ant-style injection if build.xml exists
            build_xml = os.path.join(work_dir, "build.xml")
            if os.path.isfile(build_xml):
                add_ant(build_xml, jackson_version)
            
            # Find and modify all other build files that might need Jackson dependencies
            all_build_files = find_all_build_files(work_dir)
            for build_file in all_build_files:
                if build_file.endswith('maven-build.xml') and os.path.isfile(build_file):
                    add_dependencies_to_maven_build_xml(build_file, jackson_version)
                elif build_file.endswith('build.xml') and os.path.isfile(build_file):
                    add_ant(build_file, jackson_version)
            
            # Always ensure JARs present under lib/ for Ant-driven builds
            download_jackson_jars(work_dir, jackson_version)
            
            # Fix encoding issues in all build files
            fix_encoding_in_build_files(work_dir)
            
            # Validate Jackson classpath
            if not validate_jackson_classpath(work_dir, jackson_version):
                status["stages"]["jackson"] = "fail"
                status["error"] = "jackson classpath validation failed"
                return status
                
            status["stages"]["jackson"] = "ok"
        except Exception as e:
            status["stages"]["jackson"] = "fail"
            status["error"] = f"jackson install failed: {e}"
            return status

        # Ensure helper sources and jars exist before any compile
        src_java_rel = defects4j.export(work_dir, "dir.src.classes") or "src/main/java"
        ensure_helper_sources(work_dir, src_java_rel)
        download_jackson_jars(work_dir, jackson_version)

        # Initial compile
        out_file = os.path.join(work_dir, "dump.jsonl")
        env_vars = {"OBJDUMP_OUT": out_file}
        compile_success, compile_out, compile_err = defects4j.compile(work_dir, env=env_vars)
        if not compile_success:
            status["stages"]["compile"] = "fail"
            error_details = f"stdout: {compile_out}\nstderr: {compile_err}" if compile_out or compile_err else "No detailed error information available"
            status["error"] = f"compile failed: {error_details}"
            return status
        status["stages"]["compile"] = {
            "status": "ok",
            "java_version": detect_java_version(work_dir)
        }

        # Post-compile Jackson re-injection for newly generated build files
        # Defects4J may generate defects4j.build.xml after initial compile
        try:
            inject_jackson_into_all_build_files(work_dir, jackson_version)
            # Re-validate Jackson classpath after re-injection
            if not validate_jackson_classpath(work_dir, jackson_version):
                print("Warning: Jackson classpath validation failed after re-injection")
        except Exception as e:
            print(f"Warning: Post-compile Jackson re-injection failed: {e}")

        # Diffs and instrumentation plan
        classes_dir = defects4j.export(work_dir, "dir.src.classes") or ""
        modified_classes = (defects4j.export(work_dir, "classes.modified") or "").splitlines()
        modified_classes = [s for s in (c.strip() for c in modified_classes) if s]

        def to_path(class_path: str, modified: List[str]) -> List[str]:
            result: List[str] = []
            for mc in modified:
                cp = mc.replace(".", "/")
                result.append(os.path.join(class_path, cp))
            return result

        modified_class_paths = to_path(classes_dir, modified_classes) if classes_dir and modified_classes else []

        changed: Dict[str, List[str]] = {}
        for buggy_cp in modified_class_paths:
            java_buggy = os.path.join(work_dir, buggy_cp + ".java")
            java_fixed = os.path.join(f"{work_dir}_fixed", buggy_cp + ".java")
            if not (os.path.isfile(java_buggy) and os.path.isfile(java_fixed)):
                continue
            ranges = compute_file_diff_ranges_both(java_buggy, java_fixed)
            methods = set()
            if ranges.get("left"):
                methods.update(extract_changed_methods(java_buggy, ranges["left"]))
            if ranges.get("right"):
                methods.update(extract_changed_methods(java_fixed, ranges["right"]))
            if methods:
                changed[java_buggy] = sorted(methods)

        instrumented_map: Dict[str, List[str]] = {}
        try:
            if changed:
                instrumented_map = instrument_changed_methods(changed)
            else:
                if instrument_all_modified and modified_class_paths:
                    from tree_sitter import Parser
                    from tree_sitter_languages import get_language
                    all_map: Dict[str, List[str]] = {}
                    for p in modified_class_paths:
                        jf = os.path.join(work_dir, p + ".java")
                        if not os.path.isfile(jf):
                            continue
                        try:
                            lang = get_language("java")
                            parser = Parser()
                            parser.set_language(lang)
                            with open(jf, "rb") as f:
                                s = f.read()
                            t = parser.parse(s)
                            cursor = t.walk()
                            stack = [cursor.node]
                            sigs: Set[str] = set()
                            from instrumentation.ts import method_signature_from_node
                            while stack:
                                n = stack.pop()
                                if n.type in ("method_declaration", "constructor_declaration"):
                                    sigs.add(method_signature_from_node(s, n))
                                for i in range(n.child_count):
                                    stack.append(n.child(i))
                            if sigs:
                                all_map[jf] = sorted(sigs)
                        except Exception:
                            continue
                    if all_map:
                        instrumented_map = instrument_changed_methods(all_map)
            status["stages"]["instrument"] = {
                "status": "ok",
                "methods_found": len(changed) if changed else 0,
                "methods_instrumented": sum(len(sigs) for sigs in instrumented_map.values()) if instrumented_map else 0
            }
        except Exception as e:
            status["stages"]["instrument"] = "fail"
            status["error"] = f"instrument failed: {e}"
            return status

        # Report instrumented methods (best-effort)
        try:
            flat: List[str] = []
            for fpath, sigs in instrumented_map.items():
                abs_path = os.path.abspath(fpath)
                for sig in sigs:
                    flat.append(f"{abs_path}::{sig}")
            if report_file is None:
                report_file = os.path.join(work_dir, "instrumented_methods.json")
            payload = json.dumps(sorted(flat))
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, "w", encoding="utf-8") as rf:
                rf.write(payload)
        except Exception:
            pass

        # Rebuild after instrumentation
        rebuild_success, rebuild_out, rebuild_err = defects4j.compile(work_dir, env={"OBJDUMP_OUT": os.path.join(work_dir, "dump.jsonl")})
        if not rebuild_success:
            status["stages"]["rebuild"] = "fail"
            error_details = f"stdout: {rebuild_out}\nstderr: {rebuild_err}" if rebuild_out or rebuild_err else "No detailed error information available"
            status["error"] = f"rebuild failed: {error_details}"
            return status
        status["stages"]["rebuild"] = "ok"

        # Run tests (triggering if available)
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

        # Collect dump files after test execution
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
    except Exception as e:
        try:
            log.exception("run_all_staged error")
        except Exception:
            pass
        status["error"] = str(e)
        # If nothing was set yet, mark the first pending stage as fail
        for key in ["checkout", "jackson", "compile", "instrument", "rebuild"]:
            if status["stages"].get(key) == "pending":
                status["stages"][key] = "fail"
                break
        if isinstance(status["stages"].get("tests"), dict) and status["stages"]["tests"].get("status") == "pending":
            status["stages"]["tests"]["status"] = "skipped"
        return status

