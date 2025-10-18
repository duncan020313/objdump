from typing import List, Optional, Dict, Tuple, Any
from objdump_io.shell import run
import logging


def checkout(project_id: str, bug_id: str, work_dir: str, version_suffix: str) -> bool:
    res = run(["defects4j", "checkout", "-p", project_id, "-v", f"{bug_id}{version_suffix}", "-w", work_dir])
    return res.code == 0


def compile(work_dir: str, env: Optional[Dict[str, str]] = None) -> Tuple[bool, str, str]:
    """Compile the project and return (success, stdout, stderr)."""
    log = logging.getLogger("defects4j")
    res = run(["defects4j", "compile"], cwd=work_dir, env=env)
    if res.code != 0:
        log.error("[defects4j compile] failed")
        if res.out:
            log.error(f"stdout: {res.out}")
        if res.err:
            log.error(f"stderr: {res.err}")
        return False, res.out or "", res.err or ""
    return True, res.out or "", res.err or ""


def test(work_dir: str, tests: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None) -> bool:
    log = logging.getLogger("defects4j")
    if tests:
        all_ok = True
        for entry in tests:
            res = run(["defects4j", "test", "-t", entry], cwd=work_dir, env=env)
            if res.code != 0:
                all_ok = False
                log.debug(f"[defects4j test] failed for {entry}")
                if res.out:
                    log.debug(f"stdout: {res.out}")
                if res.err:
                    log.debug(f"stderr: {res.err}")
        return all_ok
    else:
        res = run(["defects4j", "test"], cwd=work_dir, env=env)
        if res.code != 0:
            log.debug("[defects4j test] failed")
            if res.out:
                log.debug(f"stdout: {res.out}")
            if res.err:
                log.debug(f"stderr: {res.err}")
            return False
        return True


def export(work_dir: str, prop: str) -> Optional[str]:
    res = run(["defects4j", "export", "-p", prop], cwd=work_dir)
    if res.code != 0:
        return None
    return res.out.strip() or None


def get_source_classes_dir(work_dir: str) -> str:
    """
    Robustly detect the source classes directory for Java files.
    
    Uses defects4j export -p "dir.src.classes" to get the correct path,
    with fallback to common directory structures if export fails.
    
    Args:
        work_dir: Working directory of the Defects4J project
        
    Returns:
        Relative path to the source classes directory (e.g., "src/main/java" or "src/java")
    """
    # Try to get the directory from Defects4J export
    classes_dir = export(work_dir, "dir.src.classes")
    if classes_dir:
        return classes_dir
    
    # Fallback: check for common directory structures
    import os
    common_paths = [
        "src/main/java",
        "src/java", 
        "src",
        "java"
    ]
    
    for path in common_paths:
        full_path = os.path.join(work_dir, path)
        if os.path.exists(full_path) and os.path.isdir(full_path):
            # Check if it contains Java files
            for root, dirs, files in os.walk(full_path):
                if any(f.endswith('.java') for f in files):
                    return path
    
    # Default fallback
    return "src/main/java"


def get_test_classes_dir(work_dir: str) -> str:
    """
    Robustly detect the test classes directory for Java test files.
    
    Uses defects4j export -p "dir.src.tests" to get the correct path,
    with fallback to common directory structures if export fails.
    
    Args:
        work_dir: Working directory of the Defects4J project
        
    Returns:
        Relative path to the test classes directory (e.g., "src/test/java" or "test")
    """
    # Try to get the directory from Defects4J export
    tests_dir = export(work_dir, "dir.src.tests")
    if tests_dir:
        return tests_dir
    
    # Fallback: check for common directory structures
    import os
    common_paths = [
        "src/test/java",
        "test/java",
        "test",
        "tests"
    ]
    
    for path in common_paths:
        full_path = os.path.join(work_dir, path)
        if os.path.exists(full_path) and os.path.isdir(full_path):
            # Check if it contains Java files
            for root, dirs, files in os.walk(full_path):
                if any(f.endswith('.java') for f in files):
                    return path
    
    # Default fallback
    return "src/test/java"


def resolve_test_class_path(work_dir: str, test_class_name: str) -> Optional[str]:
    """
    Convert a test class name to its file path.
    
    Args:
        work_dir: Working directory of the Defects4J project
        test_class_name: Fully qualified class name (e.g., "org.apache.commons.math3.distribution.HypergeometricDistributionTest")
        
    Returns:
        Absolute path to the .java file if it exists, None otherwise
    """
    import os
    
    # Get test classes directory
    tests_dir = get_test_classes_dir(work_dir)
    
    # Convert class name to file path
    # e.g., "org.apache.commons.math3.distribution.HypergeometricDistributionTest" 
    # -> "org/apache/commons/math3/distribution/HypergeometricDistributionTest.java"
    class_path = test_class_name.replace(".", "/") + ".java"
    file_path = os.path.join(work_dir, tests_dir, class_path)
    
    # Check if file exists
    if os.path.isfile(file_path):
        return os.path.abspath(file_path)
    
    return None



def list_bug_ids(project_id: str) -> List[int]:
    """Return all bug ids for a given Defects4J project.

    Note: Defects4J typically treats all listed bugs as activated in the public dataset.
    This function intentionally does not try to distinguish activated vs. inactive,
    as doing so reliably would require additional metadata queries. Callers can still
    cap with --max-bugs-per-project.
    """
    res = run(["defects4j", "query", "-p", project_id, "-q", "bug.id"])
    if res.code != 0:
        return []
    ids: List[int] = []
    for line in (res.out or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ids.append(int(line))
        except ValueError:
            # Ignore non-integer lines
            continue
    return sorted(ids)


def info(project_id: str, bug_id: str) -> Optional[Dict[str, Any]]:
    """Get bug information from defects4j info command.
    
    Args:
        project_id: Defects4J project ID (e.g., "Math")
        bug_id: Bug ID (e.g., "104")
        
    Returns:
        Dictionary containing parsed bug information, or None if command fails
    """
    res = run(["defects4j", "info", "-p", project_id, "-b", bug_id])
    if res.code != 0:
        return None
    
    output = res.out or ""
    lines = output.splitlines()
    
    # Parse the output
    bug_info = {
        "project": project_id,
        "bug_id": bug_id,
        "revision_id": None,
        "revision_date": None,
        "bug_report_id": None,
        "bug_report_url": None,
        "root_causes": [],
        "modified_sources": []
    }
    
    current_section = None
    for i, line in enumerate(lines):
        original_line = line
        line = line.strip()
        
        if line.startswith("Revision ID (fixed version):"):
            # The value is on the next line
            if i + 1 < len(lines):
                bug_info["revision_id"] = lines[i + 1].strip()
        elif line.startswith("Revision date (fixed version):"):
            # The value is on the next line
            if i + 1 < len(lines):
                bug_info["revision_date"] = lines[i + 1].strip()
        elif line.startswith("Bug report id:"):
            # The value is on the next line
            if i + 1 < len(lines):
                bug_info["bug_report_id"] = lines[i + 1].strip()
        elif line.startswith("Bug report url:"):
            # The value is on the next line
            if i + 1 < len(lines):
                bug_info["bug_report_url"] = lines[i + 1].strip()
        elif line.startswith("Root cause in triggering tests:"):
            current_section = "root_causes"
        elif line.startswith("List of modified sources:"):
            current_section = "modified_sources"
        elif line.startswith("Summary for Bug:") or line.startswith("Summary of configuration"):
            current_section = None
        elif line.startswith("---"):
            # Only reset section if we're not in the middle of processing content
            if current_section not in ["root_causes", "modified_sources"]:
                current_section = None
        elif current_section == "root_causes" and line.startswith("- "):
            # Parse root cause line: "- org.package.Class::method --> error.message"
            parts = line[2:].split(" --> ", 1)
            if len(parts) == 2:
                test_name = parts[0].strip()
                error_message = parts[1].strip()
                bug_info["root_causes"].append({
                    "test": test_name,
                    "error": error_message
                })
            else:
                # Handle multi-line format where test is on one line and error on next
                test_name = line[2:].strip()
                # Look ahead for the error message on the next line
                current_section = "root_causes_error"
                bug_info["root_causes"].append({
                    "test": test_name,
                    "error": ""  # Will be filled in next iteration
                })
        elif current_section == "root_causes_error" and line.startswith("--> "):
            # This is the error message line following a test name
            error_message = line[4:].strip()  # Remove "--> " prefix
            if bug_info["root_causes"]:
                bug_info["root_causes"][-1]["error"] = error_message
            current_section = "root_causes"
        elif current_section == "modified_sources" and line.startswith("- "):
            # Parse modified source line: "- org.package.Class"
            source = line[2:].strip()
            bug_info["modified_sources"].append(source)
    
    return bug_info


def get_project_build_file(project_id: str) -> Optional[str]:
    """Get the project template build file path from defects4j info command.
    
    Args:
        project_id: Defects4J project ID (e.g., "Math")
        
    Returns:
        Path to the project's template build file, or None if not found
    """
    res = run(["defects4j", "info", "-p", project_id])
    if res.code != 0:
        return None
    
    output = res.out or ""
    lines = output.splitlines()
    
    # Look for "Build file:" line
    for line in lines:
        line = line.strip()
        if line.startswith("Build file:"):
            # Extract the path after "Build file:"
            build_file_path = line.split("Build file:", 1)[1].strip()
            return build_file_path
    
    return None


def classify_bug(project_id: str, bug_id: str) -> Optional[Dict[str, Any]]:
    """Classify a bug as functional or exceptional based on root cause.
    
    Args:
        project_id: Defects4J project ID (e.g., "Math")
        bug_id: Bug ID (e.g., "104")
        
    Returns:
        Dictionary containing bug info and classification, or None if info retrieval fails
    """
    bug_info = info(project_id, bug_id)
    if not bug_info:
        return None
    
    # Classify based on root cause errors
    bug_type = "exceptional"  # Default to exceptional
    
    for root_cause in bug_info["root_causes"]:
        error_message = root_cause.get("error", "")
        if "junit.framework.AssertionFailedError" in error_message:
            bug_type = "functional"
            break
    
    bug_info["type"] = bug_type
    return bug_info



