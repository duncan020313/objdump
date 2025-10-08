import argparse
from .project import run_all


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

    args = parser.parse_args()

    if args.cmd == "all":
        run_all(args.project_id, args.bug_id, args.work_dir, args.jackson_version, args.instrument_all_modified, args.report_file)


if __name__ == "__main__":
    main()


