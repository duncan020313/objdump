import tempfile
from pathlib import Path
from jackson_installer.build_systems.maven import add_dependencies


def test_add_dependencies_inserts_properties_and_deps(tmp_path: Path):
    pom = tmp_path / "pom.xml"
    pom.write_text(
        """
        <project xmlns="http://maven.apache.org/POM/4.0.0">
          <modelVersion>4.0.0</modelVersion>
        </project>
        """.strip(),
        encoding="utf-8",
    )
    add_dependencies(str(pom), "2.13.0")
    xml = pom.read_text(encoding="utf-8")
    assert "<jackson.version>2.13.0</jackson.version>" in xml
    assert "<artifactId>jackson-core</artifactId>" in xml
    assert "<artifactId>jackson-annotations</artifactId>" in xml
    assert "<artifactId>jackson-databind</artifactId>" in xml


