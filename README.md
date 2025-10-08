# jackson_installer (modular)

A modular tool to inject Jackson dependencies and instrument changed methods in Defects4J Java projects.

## Install

- Requires: Python 3.8+, `defects4j`, `tree-sitter-languages`.
- Optional: `curl` for downloading JARs (Ant projects).

## CLI

```bash
python -m jackson_installer.cli all <PROJECT> <BUG_ID> <WORK_DIR> [--jackson-version 2.13.0] [--instrument-all-modified]
```

- PROJECT: Defects4J project id (e.g., Math, Chart)
- BUG_ID: bug number (e.g., 1)
- WORK_DIR: target directory for checkout
- --instrument-all-modified: instrument all methods in modified classes when diff not found

## What it does

1. Checks out buggy and fixed versions to `<WORK_DIR>` and `<WORK_DIR>_fixed`.
2. Detects build system (Maven/Ant) and injects Jackson deps.
3. Compiles the project with `defects4j compile`.
4. Computes diffs of modified classes and extracts changed methods via Tree-sitter.
5. Injects helper sources `org.instrument` with `DumpObj` and `DebugDump`.
6. Instruments entry/exit and return points for changed methods.
7. Rebuilds and runs triggering tests (if available).

## Package layout

- `jackson_installer/cli.py`: CLI entry (subcommands ready to extend)
- `jackson_installer/project.py`: end-to-end orchestration
- `jackson_installer/defects4j.py`: checkout, export, compile, test
- `jackson_installer/build_systems/`: maven, ant, detector
- `jackson_installer/instrumentation/`: diff, tree-sitter, instrumenter, helpers
- `jackson_installer/io/`: shell, fs, net utilities
- `jackson_installer/java_templates/`: DumpObj.java, DebugDump.java

## Programmatic usage

```python
from jackson_installer.project import run_all
run_all("Math", "1", "/tmp/math-1", jackson_version="2.13.0", instrument_all_modified=True)
```

## Development

- Tests: basic unit tests for diff parsing and XML injectors under `tests/`.
- Logging: set `JI_DEBUG=1` for debug logs.

## Notes

- Maven projects rely on POM updates; Ant projects additionally download JARs into `lib/`.
- Tree-sitter must be available for Java parsing.
