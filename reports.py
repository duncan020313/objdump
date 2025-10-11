from typing import List, Dict, Any
import os
from datetime import datetime


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            import json
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _stage_cell(stages: Dict[str, Any], key: str) -> str:
    val = stages.get(key)
    if isinstance(val, dict):
        val = val.get("status")
    if val == "ok":
        return "✅"
    if val == "fail":
        return "❌"
    if val == "skipped":
        return "⏭️"
    return "–"


def write_markdown_table(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = (
        "| Project | Bug | Checkout | Jackson | Compile | Instrument | Rebuild | Tests |\n"
        "|--------:|----:|:--------:|:-------:|:-------:|:----------:|:-------:|:-----:|\n"
    )
    lines: List[str] = [header]
    for r in sorted(rows, key=lambda x: (str(x.get("project")), int(x.get("bug_id", 0)) if str(x.get("bug_id", "0")).isdigit() else 0)):
        stages = r.get("stages", {})
        line = (
            f"| {r.get('project','?')} | {r.get('bug_id','?')} | "
            f"{_stage_cell(stages,'checkout')} | {_stage_cell(stages,'jackson')} | {_stage_cell(stages,'compile')} | {_stage_cell(stages,'instrument')} | {_stage_cell(stages,'rebuild')} | {_stage_cell(stages,'tests')} |\n"
        )
        lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def append_readme_summary(readme_path: str, rows: List[Dict[str, Any]]) -> None:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    intro = f"\n\n### Defects4J Activated Bugs Matrix (latest run: {timestamp})\n\n"
    table_lines: List[str] = []
    header = (
        "| Project | Bug | Checkout | Jackson | Compile | Instrument | Rebuild | Tests |\n"
        "|--------:|----:|:--------:|:-------:|:-------:|:----------:|:-------:|:-----:|\n"
    )
    table_lines.append(header)
    for r in sorted(rows, key=lambda x: (str(x.get("project")), int(x.get("bug_id", 0)) if str(x.get("bug_id", "0")).isdigit() else 0))[:50]:
        stages = r.get("stages", {})
        line = (
            f"| {r.get('project','?')} | {r.get('bug_id','?')} | "
            f"{_stage_cell(stages,'checkout')} | {_stage_cell(stages,'jackson')} | {_stage_cell(stages,'compile')} | {_stage_cell(stages,'instrument')} | {_stage_cell(stages,'rebuild')} | {_stage_cell(stages,'tests')} |\n"
        )
        table_lines.append(line)

    try:
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(intro)
            f.writelines(table_lines)
    except FileNotFoundError:
        # If README missing, create it with the table
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# objdump\n")
            f.write(intro)
            f.writelines(table_lines)


def write_summary_statistics(path: str, rows: List[Dict[str, Any]]) -> None:
    """Write summary statistics report to file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    total_bugs = len(rows)
    if total_bugs == 0:
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Summary Statistics\n\nNo bugs tested.\n")
        return
    
    # Calculate stage success rates
    stages = ["checkout", "jackson", "compile", "instrument", "rebuild", "tests"]
    stage_stats = {}
    
    for stage in stages:
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        for row in rows:
            stage_status = row.get("stages", {}).get(stage)
            if isinstance(stage_status, dict):
                stage_status = stage_status.get("status", "pending")
            
            if stage_status == "ok":
                success_count += 1
            elif stage_status == "fail":
                fail_count += 1
            elif stage_status == "skipped":
                skip_count += 1
        
        stage_stats[stage] = {
            "success": success_count,
            "fail": fail_count,
            "skip": skip_count,
            "total": total_bugs,
            "success_rate": (success_count / total_bugs) * 100 if total_bugs > 0 else 0
        }
    
    # Calculate per-project statistics
    project_stats = {}
    for row in rows:
        project = row.get("project", "Unknown")
        if project not in project_stats:
            project_stats[project] = {"total": 0, "success": 0, "fail": 0}
        
        project_stats[project]["total"] += 1
        
        # Count as success if all stages passed
        all_passed = True
        for stage in stages:
            stage_status = row.get("stages", {}).get(stage)
            if isinstance(stage_status, dict):
                stage_status = stage_status.get("status", "pending")
            if stage_status not in ["ok", "skipped"]:
                all_passed = False
                break
        
        if all_passed:
            project_stats[project]["success"] += 1
        else:
            project_stats[project]["fail"] += 1
    
    # Write report
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Summary Statistics\n\n")
        f.write(f"**Total bugs tested:** {total_bugs}\n\n")
        
        f.write("## Stage Success Rates\n\n")
        f.write("| Stage | Success | Fail | Skip | Success Rate |\n")
        f.write("|-------|---------|------|------|-------------:|\n")
        
        for stage in stages:
            stats = stage_stats[stage]
            f.write(f"| {stage.capitalize()} | {stats['success']} | {stats['fail']} | {stats['skip']} | {stats['success_rate']:.1f}% |\n")
        
        f.write("\n## Per-Project Statistics\n\n")
        f.write("| Project | Total | Success | Fail | Success Rate |\n")
        f.write("|---------|-------|---------|------|-------------:|\n")
        
        for project, stats in sorted(project_stats.items()):
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            f.write(f"| {project} | {stats['total']} | {stats['success']} | {stats['fail']} | {success_rate:.1f}% |\n")
        
        # Overall success rate
        total_success = sum(stats["success"] for stats in project_stats.values())
        overall_success_rate = (total_success / total_bugs) * 100 if total_bugs > 0 else 0
        f.write(f"\n**Overall Success Rate:** {overall_success_rate:.1f}% ({total_success}/{total_bugs})\n")


def write_detailed_errors(path: str, rows: List[Dict[str, Any]]) -> None:
    """Write detailed error report to file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Collect all errors by stage
    stage_errors = {}
    stages = ["checkout", "jackson", "compile", "instrument", "rebuild", "tests"]
    
    for stage in stages:
        stage_errors[stage] = []
    
    # Add general errors category
    stage_errors["general"] = []
    
    for row in rows:
        project = row.get("project", "Unknown")
        bug_id = row.get("bug_id", "?")
        error = row.get("error")
        
        if error:
            stage_errors["general"].append({
                "project": project,
                "bug_id": bug_id,
                "error": error
            })
        
        stages_data = row.get("stages", {})
        for stage in stages:
            stage_status = stages_data.get(stage)
            if isinstance(stage_status, dict):
                stage_status = stage_status.get("status", "pending")
            
            if stage_status == "fail":
                stage_errors[stage].append({
                    "project": project,
                    "bug_id": bug_id,
                    "error": error or "Stage failed without specific error message"
                })
    
    # Write report
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Detailed Error Report\n\n")
        
        for stage in ["general"] + stages:
            errors = stage_errors.get(stage, [])
            if not errors:
                continue
                
            f.write(f"## {stage.capitalize()} Errors ({len(errors)} failures)\n\n")
            
            for error_info in errors:
                f.write(f"### {error_info['project']}-{error_info['bug_id']}\n\n")
                f.write(f"```\n{error_info['error']}\n```\n\n")
        
        if not any(stage_errors.values()):
            f.write("No errors recorded.\n")


