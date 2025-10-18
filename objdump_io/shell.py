import subprocess
from dataclasses import dataclass
from typing import List, Optional, Dict
import os
import logging

log = logging.getLogger("shell")

@dataclass
class CmdResult:
    code: int
    out: str
    err: str


def run(cmd: List[str], cwd: Optional[str] = None, timeout: Optional[int] = 300, env: Optional[Dict[str, str]] = None) -> CmdResult:
    """Run a command non-interactively, capturing stdout/stderr."""
    merged_env = None
    if env is not None:
        merged_env = os.environ.copy()
        merged_env.update(env)
    
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
            env=merged_env,
        )
        return CmdResult(code=proc.returncode, out=proc.stdout, err=proc.stderr)
    except subprocess.TimeoutExpired:
        log.warning(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
        return CmdResult(code=-1, out="", err=f"Command timed out after {timeout} seconds")


