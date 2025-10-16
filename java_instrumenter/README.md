# Java Instrumenter

Java-based instrumentation tool using JavaParser for AST parsing and code transformation.

## Building

```bash
cd /root/objdump/java_instrumenter
mvn clean package
```

This will create `target/instrumenter.jar` - a standalone executable JAR.

## Usage

### Instrument Methods

```bash
java -jar target/instrumenter.jar instrument <java_file> <signature1> [<signature2> ...]
```

Example:
```bash
java -jar target/instrumenter.jar instrument Sample.java "int calculate(int a, int b)"
```

### Compute Diff

```bash
java -jar target/instrumenter.jar diff <buggy_file> <fixed_file>
```

Output: JSON with left and right line ranges

### Extract Changed Methods

```bash
java -jar target/instrumenter.jar extract-methods <java_file> <start1:end1> [<start2:end2> ...]
```

Example:
```bash
java -jar target/instrumenter.jar extract-methods Sample.java 10:15 25:30
```

Output: JSON array of method signatures

## Integration with Python

The Python orchestration layer calls this tool as a subprocess:

```python
import subprocess
import json

result = subprocess.run(
    ["java", "-jar", "instrumenter.jar", "instrument", java_file] + signatures,
    capture_output=True,
    text=True
)
methods = json.loads(result.stdout)
```

## Dependencies

- JavaParser 3.25.7 (Java 8 compatible)
- Jackson 2.13.0 for JSON serialization
- Maven for building

