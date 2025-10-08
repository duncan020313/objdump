from pathlib import Path
from jackson_installer.build_systems.ant import add_dependencies


def test_add_dependencies_adds_properties_and_paths(tmp_path: Path):
    build = tmp_path / "build.xml"
    build.write_text(
        """
        <project name="x">
          <path id="compile.classpath">
          </path>
        </project>
        """.strip(),
        encoding="utf-8",
    )
    add_dependencies(str(build), "2.13.0")
    xml = build.read_text(encoding="utf-8")
    assert "jackson.version" in xml
    assert "jackson-core-2.13.0.jar" in xml
    assert "pathelement" in xml


