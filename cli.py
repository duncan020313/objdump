import argparse
import os
import csv
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from instrumentation.post_processor import post_process_dump_files
from typing import List, Dict, Any, Set, Tuple
from reports import write_jsonl, write_markdown_table
from build_systems import inject_jackson_into_defects4j_shared_build
from reports import write_summary_statistics, write_detailed_errors

from project import run_all, run_all_staged
import defects4j
import classification


def load_valid_bugs(csv_path: str = "defects4j_valids.csv") -> Dict[str, Set[int]]:
    """Load valid bug IDs from CSV file.
    
    Returns:
        Dictionary mapping project names to sets of valid bug IDs
    """
    valid_bugs = {}
    
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Will use all available bugs.")
        return {}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                project = row['project']
                bug_id = int(row['bug_id'])
                
                if project not in valid_bugs:
                    valid_bugs[project] = set()
                valid_bugs[project].add(bug_id)
        
        print(f"Loaded valid bugs from {csv_path}:")
        for project, bugs in valid_bugs.items():
            print(f"  {project}: {len(bugs)} bugs")
            
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        return {}
    
    return valid_bugs




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
    p_matrix.add_argument("--work-base", default="/tmp/objdump-d4j")
    p_matrix.add_argument("--reports-dir", default="reports")
    p_matrix.add_argument("--reports-basename", default="", help="Base name for report files; default uses timestamp")
    p_matrix.add_argument("--dumps-dir", default="/tmp/objdump_collected_dumps", help="Centralized directory for collecting all dump files")
    p_matrix.add_argument("--valid-bugs-csv", default="defects4j_valids.csv", help="CSV file containing valid bug IDs")

    p_postprocess = sub.add_parser("postprocess", help="Post-process dump files to remove MAX_DEPTH_REACHED entries")
    p_postprocess.add_argument("dump_dir", help="Directory containing dump files to process")
    p_postprocess.add_argument("--no-backup", action="store_true", help="Do not create backup files")
    p_postprocess.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    p_classify = sub.add_parser("classify", help="Classify bugs by root cause type")
    p_classify.add_argument("--projects", default="Chart,Closure,Lang,Math,Mockito,Time", help="Comma-separated list of projects (default: all)")
    p_classify.add_argument("--max-bugs-per-project", type=int, default=0, help="Maximum bugs per project (0 = no limit)")
    p_classify.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    p_classify.add_argument("--output", help="Output CSV file path (default: stdout)")
    p_classify.add_argument("--output-md", help="Output markdown table file path")
    p_classify.add_argument("--project", help="Single project ID (for backward compatibility)")
    p_classify.add_argument("--bug", help="Single bug ID (for backward compatibility)")
    p_classify.add_argument("--filter-functional", action="store_true", help="Filter functional bugs")

    args = parser.parse_args()

    if args.cmd == "all":
        run_all(args.project_id, args.bug_id, args.work_dir, args.jackson_version, args.report_file)
    elif args.cmd == "matrix":
        projects: List[str] = [p.strip() for p in args.projects.split(",") if p.strip()]
        os.makedirs(args.reports_dir, exist_ok=True)
        
        # Load valid bugs from CSV
        valid_bugs = load_valid_bugs(args.valid_bugs_csv)
        
        # Set environment variable for centralized dumps directory
        os.environ["OBJDUMP_DUMPS_DIR"] = args.dumps_dir
        print(f"Dump files will be collected to: {args.dumps_dir}")

        # Inject Jackson into Defects4J shared build files once per project
        # This is more efficient than doing it for each individual bug
        
        print("Injecting Jackson dependencies into Defects4J shared build files...")
        inject_jackson_into_defects4j_shared_build(args.jackson_version)
        print("Jackson injection completed for all projects")

        results: List[Dict[str, Any]] = []

        def job(proj: str, bug_id: int) -> Dict[str, Any]:
            work_dir = os.path.join(args.work_base, f"{proj.lower()}-{bug_id}")
            return run_all_staged(proj, str(bug_id), work_dir, args.jackson_version, skip_shared_build_injection=True)

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futures = []
            for proj in projects:
                # Use valid bugs if available, otherwise fall back to all bugs
                if proj in valid_bugs:
                    ids = sorted(list(valid_bugs[proj]))
                    print(f"Using {len(ids)} valid bugs for {proj}")
                else:
                    ids = defects4j.list_bug_ids(proj)
                    print(f"No valid bugs found for {proj}, using all {len(ids)} available bugs")
                
                if args.max_bugs_per_project > 0:
                    ids = ids[: args.max_bugs_per_project]
                    print(f"Limited to {len(ids)} bugs for {proj} (max: {args.max_bugs_per_project})")
                
                for bug_id in ids:
                    futures.append(ex.submit(job, proj, bug_id))
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                except Exception as e:
                    res = {"project": "?", "bug_id": "?", "stages": {}, "error": str(e)}
                results.append(res)


        base = args.reports_basename.strip() or f"defects4j_matrix_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        jsonl_path = os.path.join(args.reports_dir, f"{base}.jsonl")
        md_path = os.path.join(args.reports_dir, f"{base}.md")
        summary_path = os.path.join(args.reports_dir, f"{base}_summary.md")
        errors_path = os.path.join(args.reports_dir, f"{base}_errors.md")
        
        write_jsonl(jsonl_path, results)
        write_markdown_table(md_path, results, args.dumps_dir)
        
        # Write additional reports
        write_summary_statistics(summary_path, results, args.dumps_dir)
        write_detailed_errors(errors_path, results, args.dumps_dir)
    
    elif args.cmd == "postprocess":
        
        if not os.path.exists(args.dump_dir):
            print(f"Error: Directory {args.dump_dir} does not exist")
            return
        
        print(f"Post-processing dump files in {args.dump_dir}")
        stats = post_process_dump_files(args.dump_dir, backup=not args.no_backup)
        
        if args.verbose:
            print(f"Processing complete:")
            print(f"  JSONL files processed: {stats['jsonl_files_processed']}")
            print(f"  JSON files processed: {stats['json_files_processed']}")
            print(f"  Total lines processed: {stats['total_lines_processed']}")
            print(f"  Errors: {stats['errors']}")
        else:
            print(f"Processed {stats['jsonl_files_processed']} JSONL files, {stats['json_files_processed']} JSON files")
            if stats['errors'] > 0:
                print(f"Warning: {stats['errors']} errors occurred during processing")
    
    elif args.cmd == "classify":
        # Handle single bug classification (backward compatibility)
        if args.project and args.bug:
            bug_info = defects4j.classify_bug(args.project, args.bug)
            
            if not bug_info:
                print(f"Error: Failed to retrieve bug information for {args.project}-{args.bug}")
                return
        else:
            projects = [
                "Chart",
                "Cli",
                "Closure",
                "Codec",
                "Collections",
                "Compress",
                "Csv",
                "Gson",
                "JacksonCore",
                "JacksonDatabind",
                "JacksonXml",
                "Jsoup",
                "JxPath",
                "Lang",
                "Math",
                "Mockito",
                "Time"
            ]
            
            print(f"Classifying bugs for projects: {', '.join(projects)}")
            print(f"Using {args.workers} parallel workers")
            
            # Use the classification module
            all_results = classification.classify_projects(projects, args.max_bugs_per_project, args.workers)
            
        if args.filter_functional:
            all_results = classification.filter_functional_bugs(all_results)
            print(f"Filtered to {len(all_results)} functional bugs")
            
        # Write outputs
        if args.output:
            classification.write_classification_csv(args.output, all_results)
            print(f"CSV results saved to {args.output}")
        
        if args.output_md:
            classification.write_classification_markdown(args.output_md, all_results)
            print(f"Markdown results saved to {args.output_md}")
        
        print(f"Total bugs classified: {len(all_results)}")

        
if __name__ == "__main__":
    main()


