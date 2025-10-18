from typing import List, Dict, Any, Optional
import os
import glob
from datetime import datetime


def check_dump_collection_status(project_id: str, bug_id: str, dumps_base_dir: str = "/tmp/objdump_collected_dumps") -> Dict[str, Any]:
    """
    Check if dump files were collected for a specific project/bug.
    
    Args:
        project_id: Project identifier (e.g., "Math", "Chart")
        bug_id: Bug identifier (e.g., "1", "2")
        dumps_base_dir: Base directory where dumps are collected
        
    Returns:
        Dictionary with collection status information
    """
    collection_dir = os.path.join(dumps_base_dir, project_id, bug_id)
    
    if not os.path.exists(collection_dir):
        return {
            "status": "not_found",
            "collection_dir": collection_dir,
            "file_count": 0,
            "files": []
        }
    
    # Find all JSON files in the collection directory
    json_pattern = os.path.join(collection_dir, "*.json")
    json_files = glob.glob(json_pattern)
    
    if not json_files:
        return {
            "status": "empty",
            "collection_dir": collection_dir,
            "file_count": 0,
            "files": []
        }
    
    # Get file sizes and modification times
    file_info = []
    total_size = 0
    
    for file_path in json_files:
        try:
            stat = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_size = stat.st_size
            total_size += file_size
            
            file_info.append({
                "name": file_name,
                "size": file_size,
                "modified": stat.st_mtime
            })
        except OSError:
            continue
    
    return {
        "status": "collected",
        "collection_dir": collection_dir,
        "file_count": len(file_info),
        "total_size": total_size,
        "files": file_info
    }


def write_json(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        import json
        json.dump(rows, f, ensure_ascii=False, indent=2)


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


def _dump_collection_cell(project_id: str, bug_id: str, dumps_base_dir: str = "/tmp/objdump_collected_dumps") -> str:
    """Get dump collection status cell for markdown table."""
    # Ensure bug_id is a string for os.path.join
    bug_id_str = str(bug_id)
    status_info = check_dump_collection_status(project_id, bug_id_str, dumps_base_dir)
    
    if status_info["status"] == "collected":
        file_count = status_info["file_count"]
        if file_count > 0:
            return f"📁 {file_count}"
        else:
            return "📁 0"
    elif status_info["status"] == "empty":
        return "📁 0"
    else:  # not_found
        return "❌"


def write_markdown_table(path: str, rows: List[Dict[str, Any]], dumps_base_dir: str = "/tmp/objdump_collected_dumps") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = (
        "| Project | Bug | Checkout | Jackson | Compile | Instrument | Rebuild | Tests | Dumps |\n"
        "|--------:|----:|:--------:|:-------:|:-------:|:----------:|:-------:|:-----:|:-----:|\n"
    )
    lines: List[str] = [header]
    for r in sorted(rows, key=lambda x: (str(x.get("project")), int(x.get("bug_id", 0)) if str(x.get("bug_id", "0")).isdigit() else 0)):
        stages = r.get("stages", {})
        project = r.get('project', '?')
        bug_id = r.get('bug_id', '?')
        dump_cell = _dump_collection_cell(project, bug_id, dumps_base_dir)
        line = (
            f"| {project} | {bug_id} | "
            f"{_stage_cell(stages,'checkout')} | {_stage_cell(stages,'jackson')} | {_stage_cell(stages,'compile')} | {_stage_cell(stages,'instrument')} | {_stage_cell(stages,'rebuild')} | {_stage_cell(stages,'tests')} | {dump_cell} |\n"
        )
        lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def write_summary_statistics(path: str, rows: List[Dict[str, Any]], dumps_base_dir: str = "/tmp/objdump_collected_dumps") -> None:
    """Write summary statistics report to file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    total_bugs = len(rows)
    if total_bugs == 0:
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Summary Statistics\n\nNo bugs tested.\n")
        return
    
    # Calculate stage success rates
    stages = ["checkout", "jackson", "compile", "instrument", "rebuild", "tests", "dumps"]
    stage_stats = {}
    
    # Calculate dump collection statistics
    dump_stats = {
        "collected": 0,
        "empty": 0,
        "not_found": 0,
        "total_files": 0,
        "total_size": 0
    }
    
    for stage in stages:
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        for row in rows:
            if stage == "dumps":
                # Special handling for dump collection status
                project = row.get("project", "Unknown")
                bug_id = row.get("bug_id", "?")
                bug_id_str = str(bug_id)
                dump_status = check_dump_collection_status(project, bug_id_str, dumps_base_dir)
                
                if dump_status["status"] == "collected" and dump_status["file_count"] > 0:
                    success_count += 1
                else:
                    fail_count += 1
            else:
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
    
    # Calculate dump collection statistics for each bug
    for row in rows:
        project = row.get("project", "Unknown")
        bug_id = row.get("bug_id", "?")
        # Ensure bug_id is a string for os.path.join
        bug_id_str = str(bug_id)
        dump_status = check_dump_collection_status(project, bug_id_str, dumps_base_dir)
        
        if dump_status["status"] == "collected":
            dump_stats["collected"] += 1
            dump_stats["total_files"] += dump_status["file_count"]
            dump_stats["total_size"] += dump_status["total_size"]
        elif dump_status["status"] == "empty":
            dump_stats["empty"] += 1
        else:  # not_found
            dump_stats["not_found"] += 1
    
    # Calculate per-project statistics
    project_stats = {}
    for row in rows:
        project = row.get("project", "Unknown")
        if project not in project_stats:
            project_stats[project] = {"total": 0, "success": 0, "fail": 0}
        
        project_stats[project]["total"] += 1
        
        # Count as success if all stages passed AND dumps were collected
        all_passed = True
        for stage in stages:
            if stage == "dumps":
                # Check dump collection status
                bug_id_str = str(row.get("bug_id", "?"))
                dump_status = check_dump_collection_status(project, bug_id_str, dumps_base_dir)
                if not (dump_status["status"] == "collected" and dump_status["file_count"] > 0):
                    all_passed = False
                    break
            else:
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
        
        f.write("\n## Dump Collection Statistics\n\n")
        f.write(f"**Collected:** {dump_stats['collected']} bugs\n")
        f.write(f"**Empty:** {dump_stats['empty']} bugs\n")
        f.write(f"**Not Found:** {dump_stats['not_found']} bugs\n")
        f.write(f"**Total Files:** {dump_stats['total_files']}\n")
        f.write(f"**Total Size:** {dump_stats['total_size']:,} bytes ({dump_stats['total_size'] / 1024 / 1024:.2f} MB)\n")
        f.write(f"**Collection Rate:** {(dump_stats['collected'] / total_bugs) * 100:.1f}%\n\n")
        
        f.write("## Per-Project Statistics\n\n")
        f.write("| Project | Total | Success | Fail | Success Rate |\n")
        f.write("|---------|-------|---------|------|-------------:|\n")
        
        for project, stats in sorted(project_stats.items()):
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            f.write(f"| {project} | {stats['total']} | {stats['success']} | {stats['fail']} | {success_rate:.1f}% |\n")
        
        # Overall success rate
        total_success = sum(stats["success"] for stats in project_stats.values())
        overall_success_rate = (total_success / total_bugs) * 100 if total_bugs > 0 else 0
        f.write(f"\n**Overall Success Rate:** {overall_success_rate:.1f}% ({total_success}/{total_bugs})\n")


def write_detailed_errors(path: str, rows: List[Dict[str, Any]], dumps_base_dir: str = "/tmp/objdump_collected_dumps") -> None:
    """Write detailed error report to file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Collect all errors by stage
    stage_errors = {}
    stages = ["checkout", "jackson", "compile", "instrument", "rebuild", "tests", "dumps"]
    
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
            if stage == "dumps":
                # Check dump collection status
                bug_id_str = str(bug_id)
                dump_status = check_dump_collection_status(project, bug_id_str, dumps_base_dir)
                if not (dump_status["status"] == "collected" and dump_status["file_count"] > 0):
                    stage_errors[stage].append({
                        "project": project,
                        "bug_id": bug_id,
                        "error": f"No dumps collected (status: {dump_status['status']}, files: {dump_status['file_count']})"
                    })
            else:
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


