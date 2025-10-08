from typing import List, Optional
from .io.shell import run


def checkout(project_id: str, bug_id: str, work_dir: str, version_suffix: str) -> bool:
    res = run(["defects4j", "checkout", "-p", project_id, "-v", f"{bug_id}{version_suffix}", "-w", work_dir])
    return res.code == 0


def compile(work_dir: str) -> bool:
    res = run(["defects4j", "compile"], cwd=work_dir)
    return res.code == 0


def test(work_dir: str, tests: Optional[List[str]] = None) -> bool:
    if tests:
        joined = ",".join(tests)
        res = run(["defects4j", "test", "-t", joined], cwd=work_dir)
    else:
        res = run(["defects4j", "test"], cwd=work_dir)
    return res.code == 0


def export(work_dir: str, prop: str) -> Optional[str]:
    res = run(["defects4j", "export", "-p", prop], cwd=work_dir)
    if res.code != 0:
        return None
    return res.out.strip() or None


