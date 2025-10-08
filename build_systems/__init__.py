from pathlib import Path
from typing import Optional

from jackson_installer.types import BuildSystem


def detect(project_dir: str) -> Optional[BuildSystem]:
    """Detect build system based on presence of build files.

    Returns BuildSystem or None if unknown.
    """
    p = Path(project_dir)
    if (p / "pom.xml").is_file():
        return BuildSystem.MAVEN
    if (p / "build.xml").is_file():
        return BuildSystem.ANT
    return None


