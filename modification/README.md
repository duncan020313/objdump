Change d4j-test in /defects4j/framework/bin/d4j/d4j-test into modification/dj4-test
It ignores compilation when test is specified by -t option.

```bash
for d in /defects4j/framework/projects/*/lib/; do cp .cache/jars/*.jar "$d"; done
test $(ls -l /defects4j/framework/projects/*/lib/jackson-*.jar | wc -l) -eq 45 || { echo "Expected 45 Jackson JAR files, but found $(ls -l /defects4j/framework/projects/*/lib/jackson-*.jar | wc -l)"; exit 1; }
cp modification/dj4-test /defects4j/framework/bin/d4j/d4j-test
cp modification/Collections.build.xml /defects4j/framework/projects/Collections/Collections.build.xml
```