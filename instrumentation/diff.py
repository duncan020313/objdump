from typing import Dict, List, Tuple
import os
import instrumentation.ts as ts  # for typing-only coupling avoidance
from subprocess import run as sprun, PIPE


def parse_unified_diff_hunks_both(diff_text: str) -> Dict[str, List[Tuple[int, int]]]:
    """Parse unified diff; return {'left': [(s,e)], 'right': [(s,e)]}."""
    left_hunks: List[Tuple[int, int]] = []
    right_hunks: List[Tuple[int, int]] = []
    
    lines = diff_text.splitlines()
    
    for i, line in enumerate(lines):
        # Look for hunk header
        if line.startswith("@@ ") and "@@" in line:
            try:
                header = line.split("@@")[1].strip()
                parts = header.split()
                if len(parts) < 2:
                    continue
                    
                left, right = parts[0].lstrip("-"), parts[1].lstrip("+")
                
                # Parse starting line numbers
                if "," in left:
                    lstart_s, _ = left.split(",", 1)
                    lstart = int(lstart_s)
                else:
                    lstart = int(left)
                    
                if "," in right:
                    rstart_s, _ = right.split(",", 1)
                    rstart = int(rstart_s)
                else:
                    rstart = int(right)
                
                # Track actual changed lines within this hunk
                left_changed_lines = []
                right_changed_lines = []
                current_left_line = lstart
                current_right_line = rstart
                
                # Process lines within this hunk
                for j in range(i + 1, len(lines)):
                    hunk_line = lines[j]
                    
                    # Check if we've reached the next hunk
                    if hunk_line.startswith("@@ "):
                        break
                        
                    # Process diff line based on prefix
                    if hunk_line.startswith("-"):
                        # Deletion from left (buggy) file
                        left_changed_lines.append(current_left_line)
                        current_left_line += 1
                    elif hunk_line.startswith("+"):
                        # Addition to right (fixed) file
                        right_changed_lines.append(current_right_line)
                        current_right_line += 1
                    elif hunk_line.startswith(" "):
                        # Context line - present in both files
                        current_left_line += 1
                        current_right_line += 1
                    elif hunk_line.startswith("\\"):
                        # No newline at end of file marker
                        pass
                    else:
                        # Other lines (like diff headers) - skip
                        pass
                
                # Build ranges from changed lines
                if left_changed_lines:
                    left_ranges = _build_ranges_from_lines(left_changed_lines)
                    left_hunks.extend(left_ranges)
                    
                if right_changed_lines:
                    right_ranges = _build_ranges_from_lines(right_changed_lines)
                    right_hunks.extend(right_ranges)
                    
            except Exception:
                continue
    
    return {"left": left_hunks, "right": right_hunks}


def _build_ranges_from_lines(changed_lines: List[int]) -> List[Tuple[int, int]]:
    """Build contiguous ranges from a list of line numbers."""
    if not changed_lines:
        return []
    
    changed_lines.sort()
    ranges = []
    start = changed_lines[0]
    end = start
    
    for line in changed_lines[1:]:
        if line == end + 1:
            # Contiguous line
            end = line
        else:
            # Gap found, close current range and start new one
            ranges.append((start, end))
            start = line
            end = line
    
    # Add the last range
    ranges.append((start, end))
    return ranges


def compute_file_diff_ranges_both(buggy_file: str, fixed_file: str) -> Dict[str, List[Tuple[int, int]]]:
    proc = sprun(["diff", "-U", "3", buggy_file, fixed_file], stdout=PIPE, stderr=PIPE, text=True)
    if proc.returncode == 0:
        return {"left": [], "right": []}
    return parse_unified_diff_hunks_both(proc.stdout)
