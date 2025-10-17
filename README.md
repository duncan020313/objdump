# objdump

A modular tool to dump object state and method invocations in Defects4J Java projects.

## Install

- Requires: Python 3.8+, Java 8+, Maven, `defects4j`
- Optional: `curl` for downloading JARs (Ant projects)

### Building the Java Instrumenter

The project uses a Java-based instrumenter for AST parsing and code transformation:

```bash
cd java_instrumenter
mvn clean package
```

This creates `java_instrumenter/target/instrumenter.jar` which is automatically used by Python.

## CLI

```bash
python -m objdump.cli all <PROJECT> <BUG_ID> <WORK_DIR> [--jackson-version 2.13.0] [--report-file <PATH>]
python -m objdump.cli matrix [--projects "Chart,Closure,Lang,Math,Mockito,Time"] [--max-bugs-per-project 0] [--workers 4] [--jackson-version 2.13.0] [--work-base /tmp/objdump-d4j] [--reports-dir reports]
python -m objdump.cli classify [--projects "Chart,Closure,Lang,Math,Mockito,Time"] [--max-bugs-per-project 0] [--workers 4] [--output <PATH>]
```

- PROJECT: Defects4J project id (e.g., Math, Chart)
- BUG_ID: bug number (e.g., 1)
- WORK_DIR: target directory for checkout
- --instrument-all-modified: instrument all methods in modified classes when diff not found
- --report-file: write instrumented method paths JSON to this file (also printed)

### Bug Classification

The `classify` command analyzes Defects4J bug information and classifies bugs based on their root cause:

- **Functional bugs**: Contain `junit.framework.AssertionFailedError` in root cause
- **Exceptional bugs**: All other error types

The command supports both single bug classification (backward compatibility) and batch processing. By default, it processes **all available bugs** for each project (not limited to a predefined valid bugs list):

```bash
# Batch classification - all projects and all bugs (CSV output to stdout)
python -m objdump.cli classify

# Classify specific projects (all bugs)
python -m objdump.cli classify --projects Math,Chart

# Limit bugs per project
python -m objdump.cli classify --projects Math --max-bugs-per-project 10

# Save to CSV file
python -m objdump.cli classify --output classifications.csv

# Save to markdown table
python -m objdump.cli classify --output-md classifications.md

# Save to both CSV and markdown
python -m objdump.cli classify --output classifications.csv --output-md classifications.md

# Single bug classification (backward compatibility)
python -m objdump.cli classify --project Math --bug 104
```

**Output Formats:**

**CSV Format:**
- `project`: Project name
- `bug_id`: Bug ID
- `type`: Classification (functional/exceptional)
- `bug_report_id`: Bug report ID
- `revision_id`: Git revision ID
- `revision_date`: Revision date
- `bug_report_url`: Bug report URL
- `root_causes_count`: Number of root causes
- `modified_sources_count`: Number of modified sources
- `root_causes`: Semicolon-separated list of test:error pairs
- `modified_sources`: Semicolon-separated list of modified classes
- `error`: Error message if classification failed

**Markdown Format:**
- Summary section with counts by bug type
- Table with Project, Bug ID, Type, Bug Report, Root Causes, and Modified Sources
- Error section for failed classifications
- Human-readable format suitable for documentation

## Architecture

The system uses a **hybrid Java + Python architecture**:

- **Java**: Handles AST parsing, diff analysis, JavaDoc extraction, and code transformation using JavaParser
- **Python**: Handles project orchestration, build system management, and test execution

This separation provides better reliability for Java code transformation while keeping Python for high-level workflow.

## What it does

1. Checks out buggy and fixed versions to `<WORK_DIR>` and `<WORK_DIR>_fixed`.
2. Detects build system (Maven/Ant) and injects Jackson deps.
3. Compiles the project with `defects4j compile`.
4. Computes diffs of modified classes and extracts changed methods via Java-based instrumenter.
5. Injects helper sources `org.instrument` with `DumpObj`, `DebugDump`, and `DumpWrapper`.
6. Instruments changed methods by transforming the AST to add entry/exit logging and exception handling.
7. Emits JSON report of instrumented methods with code, JavaDoc, and signatures to `--report-file` (or `<WORK_DIR>/instrumented_methods.json`).
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

## Report Format

The tool generates `instrumented_methods.json` with detailed information about each instrumented method:

```json
[
  {
    "file": "/absolute/path/to/File.java",
    "signature": "returnType methodName(paramTypes)",
    "code": "full method source code including annotations",
    "javadoc": {
      "description": "Main description text",
      "params": {
        "paramName": "parameter description"
      },
      "returns": "return value description",
      "throws": {
        "ExceptionType": "exception description"
      }
    }
  }
]
```

If a method has no JavaDoc, the `javadoc` field will be `null`.

## Package layout

- `objdump/cli.py`: CLI entry (subcommands ready to extend)
- `objdump/project.py`: end-to-end orchestration
- `objdump/defects4j.py`: checkout, export, compile, test
- `objdump/build_systems/`: maven, ant, detector
- `objdump/instrumentation/`: instrumenter (Python wrapper), helpers
- `objdump/io/`: shell, fs, net utilities
- `objdump/java_templates/`: DumpObj.java, DebugDump.java, DumpWrapper.java
- `java_instrumenter/`: Java-based AST parser and code transformer (JavaParser)
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


### Defects4J Activated Bugs Matrix (latest run: 2025-10-17 00:56 UTC)

| Project | Bug | Checkout | Jackson | Compile | Instrument | Rebuild | Tests | Dumps |
|--------:|----:|:--------:|:-------:|:-------:|:----------:|:-------:|:-----:|:-----:|
| Math | 2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 6 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 28 |
| Math | 7 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 9 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 10 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 11 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 12 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 15 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 16 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 2 |
| Math | 17 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 18 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 20 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 21 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 2 |
| Math | 22 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 2 |
| Math | 23 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 24 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 25 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 26 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 27 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 29 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 30 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 33 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 34 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 35 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 2 |
| Math | 36 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 37 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 4 |
| Math | 39 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 41 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 42 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 43 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 6 |
| Math | 44 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 45 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 46 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 2 |
| Math | 47 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 2 |
| Math | 50 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 52 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 53 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 54 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 55 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 56 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 57 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 59 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 62 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 63 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 1 |
| Math | 64 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 2 |
| Math | 65 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 66 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 4 |
| Math | 67 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 0 |
| Math | 68 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 📁 2 |
