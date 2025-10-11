# objdump

A modular tool to dump object state and method invocations in Defects4J Java projects.

## Install

- Requires: Python 3.8+, `defects4j`, `tree-sitter-languages`.
- Optional: `curl` for downloading JARs (Ant projects).

## CLI

```bash
python -m objdump.cli all <PROJECT> <BUG_ID> <WORK_DIR> [--jackson-version 2.13.0] [--instrument-all-modified] [--report-file <PATH>]
python -m objdump.cli matrix [--projects "Chart,Closure,Lang,Math,Mockito,Time"] [--max-bugs-per-project 0] [--workers 4] [--jackson-version 2.13.0] [--instrument-all-modified] [--work-base /tmp/objdump-d4j] [--reports-dir reports]
```

- PROJECT: Defects4J project id (e.g., Math, Chart)
- BUG_ID: bug number (e.g., 1)
- WORK_DIR: target directory for checkout
- --instrument-all-modified: instrument all methods in modified classes when diff not found
- --report-file: write instrumented method paths JSON to this file (also printed)

## What it does

1. Checks out buggy and fixed versions to `<WORK_DIR>` and `<WORK_DIR>_fixed`.
2. Detects build system (Maven/Ant) and injects Jackson deps.
3. Compiles the project with `defects4j compile`.
4. Computes diffs of modified classes and extracts changed methods via Tree-sitter.
5. Injects helper sources `org.instrument` with `DumpObj`, `DebugDump`, and `DumpWrapper`.
6. Instruments changed methods using a wrapping approach that automatically handles entry/exit logging and exception propagation.
7. Emits JSON list of instrumented method paths as `<abs_path>::<signature>` to stdout and to `--report-file` (or `<WORK_DIR>/instrumented_methods.json`).
8. Rebuilds and runs triggering tests (if available). For each triggering test, writes a JSONL dump to `<WORK_DIR>/dumps/<TEST_NAME>.jsonl`. If no triggering tests are available, writes a single dump to `<WORK_DIR>/dump.jsonl` when running the full suite.

## Instrumentation Approach

The tool uses a **wrapping-based instrumentation** strategy that is simpler and more robust than direct code insertion:

- **Method Wrapping**: Target methods are wrapped with `DumpWrapper.wrap()` or `DumpWrapper.wrapVoid()` calls
- **Automatic Exception Handling**: The wrapper automatically handles exceptions and ensures exit logging
- **Parameter Extraction**: Uses Java Reflection API to extract parameter names at runtime (requires `-parameters` compiler flag)
- **Single-Pass Processing**: Only one AST parsing pass needed, reducing complexity and potential errors
- **Constructor Support**: Handles constructors with `super()`/`this()` calls by preserving them outside the wrapper

### Example Transformation

```java
// Original method
public String processData(String input, int count) {
    return input + "_" + count;
}

// After instrumentation
@DumpObj
public String processData(String input, int count) {
    return DumpWrapper.wrap(this, "processData", 
        new Object[]{input, count}, 
        () -> {
            return input + "_" + count;
        });
}
```

### DumpWrapper API

- `DumpWrapper.wrap(Object self, String methodName, Object[] params, Supplier<T> method)`: For methods with return values
- `DumpWrapper.wrapVoid(Object self, String methodName, Object[] params, Runnable method)`: For void methods and constructors
- Automatic parameter name extraction using Java Reflection
- Automatic entry/exit logging with exception handling

## Package layout

- `objdump/cli.py`: CLI entry (subcommands ready to extend)
- `objdump/project.py`: end-to-end orchestration
- `objdump/defects4j.py`: checkout, export, compile, test
- `objdump/build_systems/`: maven, ant, detector
- `objdump/instrumentation/`: diff, tree-sitter, instrumenter, helpers
- `objdump/io/`: shell, fs, net utilities
- `objdump/java_templates/`: DumpObj.java, DebugDump.java, DumpWrapper.java
- `tests/`: unit and integration tests for instrumentation

## Programmatic usage

```python
from objdump.project import run_all
run_all("Math", "1", "/tmp/math-1", jackson_version="2.13.0", instrument_all_modified=True, report_file="/tmp/instrumented.json")
```

## Development

- Tests: basic unit tests for diff parsing and XML injectors under `tests/`.
- Logging: set `JI_DEBUG=1` for debug logs.

## Notes

- Maven projects rely on POM updates; Ant projects additionally download JARs into `lib/`.
- Tree-sitter must be available for Java parsing.
