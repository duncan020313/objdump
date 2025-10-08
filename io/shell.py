import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CmdResult:
    code: int
    out: str
    err: str


def run(cmd: List[str], cwd: Optional[str] = None, timeout: Optional[int] = 300) -> CmdResult:
    """Run a command non-interactively, capturing stdout/stderr."""
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    return CmdResult(code=proc.returncode, out=proc.stdout, err=proc.stderr)


