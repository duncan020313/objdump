import argparse
import logging
import os
import csv
import subprocess
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from instrumentation.post_processor import post_process_dump_files
from typing import List, Dict, Any, Set, Tuple
from reports import write_json, write_markdown_table
from reports import write_summary_statistics, write_detailed_errors
from tqdm import tqdm

from project import run_all, run_all_staged
import defects4j
import classification
from logging_setup import configure_logging
import merger

PROJECTS = [
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

def build_java_instrumenter() -> bool:
    """Build the Java instrumenter using Maven.

    Returns:
        True if build succeeded, False otherwise
    """
    log = logging.getLogger("build_java_instrumenter")
    instrumenter_dir = os.path.join(os.path.dirname(__file__), "java_instrumenter")

    log.info("Building Java instrumenter...")
    result = subprocess.run(
        ["mvn", "clean", "package", "-q"],
        cwd=instrumenter_dir,
        capture_output=False,
    )

    if result.returncode != 0:
        log.error("Java instrumenter build failed")
        sys.exit(1)

    log.info("Java instrumenter built successfully")
    return True


def load_valid_bugs(csv_path: str = "defects4j_valids.csv") -> Dict[str, Set[int]]:
    """Load valid bug IDs from CSV file.

    Returns:
        Dictionary mapping project names to sets of valid bug IDs
    """
    log = logging.getLogger("load_valid_bugs")
    valid_bugs = {}

    if not os.path.exists(csv_path):
        log.warning(f"Warning: {csv_path} not found. Will use all available bugs.")
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

        log.info(f"Loaded valid bugs from {csv_path}:")
        for project, bugs in valid_bugs.items():
            log.info(f"  {project}: {len(bugs)} bugs")

    except Exception as e:
        log.error(f"Error loading {csv_path}: {e}")
        return {}

    return valid_bugs




def main() -> None:
    parser = argparse.ArgumentParser(description="Inject Jackson and instrument Defects4J projects")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("all", help="Run full workflow: checkout, inject, instrument, tests")
    p_all.add_argument("project_id")
    p_all.add_argument("bug_id")
    p_all.add_argument("work_dir")
    p_all.add_argument("--jackson-version", dest="jackson_version", default="2.13.0")
    p_all.add_argument("--instrument-all-modified", action="store_true")
    p_all.add_argument("--report-file", dest="report_file")

    p_matrix = sub.add_parser("matrix", help="Run across activated bugs and summarize results")
    p_matrix.add_argument("--projects", default=",".join(PROJECTS))
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
    p_classify.add_argument("--projects", default=",".join(PROJECTS), help="Comma-separated list of projects")
    p_classify.add_argument("--max-bugs-per-project", type=int, default=0, help="Maximum bugs per project (0 = no limit)")
    p_classify.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    p_classify.add_argument("--output", help="Output CSV file path (default: stdout)")
    p_classify.add_argument("--output-md", help="Output markdown table file path")
    p_classify.add_argument("--project", help="Single project ID (for backward compatibility)")
    p_classify.add_argument("--bug", help="Single bug ID (for backward compatibility)")
    p_classify.add_argument("--filter-functional", action="store_true", help="Filter functional bugs")

    p_merge = sub.add_parser("merge", help="Merge JSON/JSONL files from directory into single JSON file")
    p_merge.add_argument("target_dir", help="Directory to scan for JSON/JSONL files")
    p_merge.add_argument("--output", "-o", required=True, help="Output JSON file path")

    args = parser.parse_args()

    configure_logging(debug=args.debug)
    log = logging.getLogger("cli")

    if not build_java_instrumenter():
        log.error("Failed to build Java instrumenter. Exiting.")
        sys.exit(1)


    if args.cmd == "all":
        run_all(args.project_id, args.bug_id, args.work_dir, args.jackson_version, args.report_file)
    elif args.cmd == "matrix":
        projects: List[str] = [p.strip() for p in args.projects.split(",") if p.strip()]
        if not projects:
            projects = PROJECTS

        os.makedirs(args.reports_dir, exist_ok=True)

        # Load valid bugs from CSV
        valid_bugs = load_valid_bugs(args.valid_bugs_csv)

        # Set environment variable for centralized dumps directory
        os.environ["OBJDUMP_DUMPS_DIR"] = args.dumps_dir
        log.info(f"Dump files will be collected to: {args.dumps_dir}")

        results: List[Dict[str, Any]] = []

        # Calculate total number of bugs to process
        total_bugs = 0
        bug_tasks = []  # List of (project, bug_id) tuples

        for proj in projects:
            # Use valid bugs if available, otherwise fall back to all bugs
            if proj in valid_bugs:
                ids = sorted(list(valid_bugs[proj]))
                log.info(f"Using {len(ids)} valid bugs for {proj}")
            else:
                ids = defects4j.list_bug_ids(proj)
                log.info(f"No valid bugs found for {proj}, using all {len(ids)} available bugs")

            if args.max_bugs_per_project > 0:
                ids = ids[: args.max_bugs_per_project]
                log.info(f"Limited to {len(ids)} bugs for {proj} (max: {args.max_bugs_per_project})")

            for bug_id in ids:
                bug_tasks.append((proj, bug_id))
                total_bugs += 1

        def job(proj: str, bug_id: int) -> Dict[str, Any]:
            work_dir = os.path.join(args.work_base, f"{proj.lower()}-{bug_id}")
            return run_all_staged(proj, str(bug_id), work_dir, args.jackson_version, skip_shared_build_injection=True)

        progress_bar = tqdm(
            total=total_bugs,
            desc="Processing bugs",
            unit="bug",
            position=0,
            leave=True,
            dynamic_ncols=True,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
            colour='green',
            file=sys.stdout
        )

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futures = []
            for proj, bug_id in bug_tasks:
                futures.append(ex.submit(job, proj, bug_id))

            for fut in as_completed(futures):
                try:
                    res = fut.result()
                except Exception as e:
                    res = {"project": "?", "bug_id": "?", "stages": {}, "error": str(e)}
                results.append(res)
                progress_bar.update(1)

                # Update progress bar description with current status
                completed = len(results)
                progress_bar.set_description(f"Processing bugs ({completed}/{total_bugs})")

        progress_bar.close()

        # Log completion summary
        successful = len([r for r in results if r["error"] is None])
        failed = len([r for r in results if r["error"] is not None])
        log.info(f"Matrix processing completed: {successful} successful, {failed} failed out of {total_bugs} total bugs")

        base = args.reports_basename.strip() or f"defects4j_matrix_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        json_path = os.path.join(args.reports_dir, f"{base}.json")
        md_path = os.path.join(args.reports_dir, f"{base}.md")
        summary_path = os.path.join(args.reports_dir, f"{base}_summary.md")
        errors_path = os.path.join(args.reports_dir, f"{base}_errors.md")

        write_json(json_path, results)
        write_markdown_table(md_path, results, args.dumps_dir)

        # Write additional reports
        write_summary_statistics(summary_path, results, args.dumps_dir)
        write_detailed_errors(errors_path, results, args.dumps_dir)

    elif args.cmd == "postprocess":

        if not os.path.exists(args.dump_dir):
            log.error(f"Error: Directory {args.dump_dir} does not exist")
            return

        log.info(f"Post-processing dump files in {args.dump_dir}")
        stats = post_process_dump_files(args.dump_dir, backup=not args.no_backup)

        if args.verbose:
            log.info(f"Processing complete:")
            log.info(f"  JSON files processed: {stats['jsonl_files_processed']}")
            log.info(f"  JSON files processed: {stats['json_files_processed']}")
            log.info(f"  Total lines processed: {stats['total_lines_processed']}")
            log.info(f"  Errors: {stats['errors']}")
        else:
            log.info(f"Processed {stats['jsonl_files_processed']} JSON files, {stats['json_files_processed']} JSON files")
            if stats['errors'] > 0:
                log.warning(f"Warning: {stats['errors']} errors occurred during processing")

    elif args.cmd == "classify":
        # Handle single bug classification (backward compatibility)
        if args.project and args.bug:
            bug_info = defects4j.classify_bug(args.project, args.bug)

            if not bug_info:
                log.error(f"Error: Failed to retrieve bug information for {args.project}-{args.bug}")
                return
        else:
            log.info(f"Classifying bugs for projects: {', '.join(PROJECTS)}")
            log.info(f"Using {args.workers} parallel workers")

            # Use the classification module
            all_results = classification.classify_projects(PROJECTS, args.max_bugs_per_project, args.workers)

        if args.filter_functional:
            all_results = classification.filter_functional_bugs(all_results)
            log.info(f"Filtered to {len(all_results)} functional bugs")

        # Write outputs
        if args.output:
            classification.write_classification_csv(args.output, all_results)
            log.info(f"CSV results saved to {args.output}")

        if args.output_md:
            classification.write_classification_markdown(args.output_md, all_results)
            log.info(f"Markdown results saved to {args.output_md}")

        log.info(f"Total bugs classified: {len(all_results)}")

    elif args.cmd == "merge":
        try:
            stats = merger.merge_json_files(args.target_dir, args.output)
            log.info(f"Merge completed: {stats['json_count']} JSON files processed")
            log.info(f"Output size: {stats['output_size']:,} bytes")
            if stats['errors'] > 0:
                log.warning(f"Errors encountered: {stats['errors']}")
        except Exception as e:
            log.error(f"Merge failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()


