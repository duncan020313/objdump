Change d4j-test in /defects4j/framework/bin/d4j/d4j-test into modification/dj4-test
It ignores compilation when test is specified by -t option.

```bash
for d in /defects4j/framework/projects/*/lib/; do cp .cache/jars/*.jar "$d"; done
# Check if the files are copied
ls -l /defects4j/framework/projects/*/lib/jackson-*.jar | wc -l # Should be 45 (3 * 15)
# Copy the modified d4j-test
cp modification/dj4-test /defects4j/framework/bin/d4j/d4j-test
```