from typing import List, Optional, Dict, Tuple
from objdump_io.shell import run


def checkout(project_id: str, bug_id: str, work_dir: str, version_suffix: str) -> bool:
    res = run(["defects4j", "checkout", "-p", project_id, "-v", f"{bug_id}{version_suffix}", "-w", work_dir])
    return res.code == 0


def compile(work_dir: str, env: Dict[str, str] = None) -> Tuple[bool, str, str]:
    """Compile the project and return (success, stdout, stderr)."""
    res = run(["defects4j", "compile"], cwd=work_dir, env=env)
    if res.code != 0:
        print("[defects4j compile] failed")
        if res.out:
            print(res.out)
        if res.err:
            print(res.err)
        return False, res.out or "", res.err or ""
    return True, res.out or "", res.err or ""


def test(work_dir: str, tests: Optional[List[str]] = None, env: Dict[str, str] = None) -> bool:
    if tests:
        all_ok = True
        for entry in tests:
            res = run(["defects4j", "test", "-t", entry], cwd=work_dir, env=env)
            if res.code != 0:
                all_ok = False
                print("[defects4j test] failed for", entry)
                if res.out:
                    print(res.out)
                if res.err:
                    print(res.err)
        return all_ok
    else:
        res = run(["defects4j", "test"], cwd=work_dir, env=env)
        if res.code != 0:
            print("[defects4j test] failed")
            if res.out:
                print(res.out)
            if res.err:
                print(res.err)
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

