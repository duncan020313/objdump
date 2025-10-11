import argparse
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from project import run_all, run_all_staged
import defects4j



def main() -> None:
    parser = argparse.ArgumentParser(description="Inject Jackson and instrument Defects4J projects")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("all", help="Run full workflow: checkout, inject, instrument, tests")
    p_all.add_argument("project_id")
    p_all.add_argument("bug_id")
    p_all.add_argument("work_dir")
    p_all.add_argument("--jackson-version", dest="jackson_version", default="2.13.0")
    p_all.add_argument("--instrument-all-modified", action="store_true")
    p_all.add_argument("--report-file", dest="report_file")

    p_matrix = sub.add_parser("matrix", help="Run across activated bugs and summarize results")
    p_matrix.add_argument("--projects", default="Chart,Closure,Lang,Math,Mockito,Time")
    p_matrix.add_argument("--max-bugs-per-project", type=int, default=0, help="0 means no cap")
    p_matrix.add_argument("--workers", type=int, default=4)
    p_matrix.add_argument("--jackson-version", dest="jackson_version", default="2.13.0")
    p_matrix.add_argument("--instrument-all-modified", action="store_true")
    p_matrix.add_argument("--work-base", default="/tmp/objdump-d4j")
    p_matrix.add_argument("--reports-dir", default="reports")
    p_matrix.add_argument("--reports-basename", default="", help="Base name for report files; default uses timestamp")

    args = parser.parse_args()

    if args.cmd == "all":
        run_all(args.project_id, args.bug_id, args.work_dir, args.jackson_version, args.instrument_all_modified, args.report_file)
    elif args.cmd == "matrix":
        projects: List[str] = [p.strip() for p in args.projects.split(",") if p.strip()]
        os.makedirs(args.reports_dir, exist_ok=True)

        results: List[Dict[str, Any]] = []

        def job(proj: str, bug_id: int) -> Dict[str, Any]:
            work_dir = os.path.join(args.work_base, f"{proj.lower()}-{bug_id}")
            return run_all_staged(proj, str(bug_id), work_dir, args.jackson_version, args.instrument_all_modified)

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futures = []
            for proj in projects:
                ids = defects4j.list_bug_ids(proj)
                if args.max_bugs_per_project > 0:
                    ids = ids[: args.max_bugs_per_project]
                for bug_id in ids:
                    futures.append(ex.submit(job, proj, bug_id))
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                except Exception as e:
                    res = {"project": "?", "bug_id": "?", "stages": {}, "error": str(e)}
                results.append(res)

        # Write JSONL and Markdown table
        from datetime import datetime
        from reports import write_jsonl, write_markdown_table, append_readme_summary

        base = args.reports_basename.strip() or f"defects4j_matrix_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        jsonl_path = os.path.join(args.reports_dir, f"{base}.jsonl")
        md_path = os.path.join(args.reports_dir, f"{base}.md")
        write_jsonl(jsonl_path, results)
        write_markdown_table(md_path, results)
        append_readme_summary("README.md", results)


if __name__ == "__main__":
    main()


