from typing import List, Optional
from objdump_io.shell import run
from typing import Dict


def checkout(project_id: str, bug_id: str, work_dir: str, version_suffix: str) -> bool:
    res = run(["defects4j", "checkout", "-p", project_id, "-v", f"{bug_id}{version_suffix}", "-w", work_dir])
    return res.code == 0


def compile(work_dir: str, env: Dict[str, str] = None) -> bool:
    res = run(["defects4j", "compile"], cwd=work_dir, env=env)
    if res.code != 0:
        print("[defects4j compile] failed")
        if res.out:
            print(res.out)
        if res.err:
            print(res.err)
        return False
    return True


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

