from typing import Dict, List, Tuple
import instrumentation.ts as ts  # for typing-only coupling avoidance
from subprocess import run as sprun, PIPE


def parse_unified_diff_hunks_both(diff_text: str) -> Dict[str, List[Tuple[int, int]]]:
    """Parse -U0 unified diff; return {'left': [(s,e)], 'right': [(s,e)]}."""
    left_hunks: List[Tuple[int, int]] = []
    right_hunks: List[Tuple[int, int]] = []
    for line in diff_text.splitlines():
        if line.startswith("@@ ") and "@@" in line:
            try:
                header = line.split("@@")[1].strip()
                parts = header.split()
                if len(parts) < 2:
                    continue
                left, right = parts[0].lstrip("-"), parts[1].lstrip("+")
                if "," in left:
                    lstart_s, lcount_s = left.split(",", 1)
                    lstart, lcount = int(lstart_s), int(lcount_s)
                else:
                    lstart, lcount = int(left), 1
                if "," in right:
                    rstart_s, rcount_s = right.split(",", 1)
                    rstart, rcount = int(rstart_s), int(rcount_s)
                else:
                    rstart, rcount = int(right), 1
                if lcount > 0:
                    lend = lstart + (lcount - 1)
                    left_hunks.append((lstart, max(lend, lstart)))
                if rcount > 0:
                    rend = rstart + (rcount - 1)
                    right_hunks.append((rstart, max(rend, rstart)))
            except Exception:
                continue
    return {"left": left_hunks, "right": right_hunks}


def compute_file_diff_ranges_both(buggy_file: str, fixed_file: str) -> Dict[str, List[Tuple[int, int]]]:
    proc = sprun(["diff", "-U", "0", buggy_file, fixed_file], stdout=PIPE, stderr=PIPE, text=True)
    if proc.returncode == 0:
        return {"left": [], "right": []}
    return parse_unified_diff_hunks_both(proc.stdout)


