from pathlib import Path
from typing import Optional, List
import glob
import logging
from jt_types import BuildSystem

log = logging.getLogger(__name__)

def detect(project_dir: str) -> Optional[BuildSystem]:
    """Detect build system based on presence of build files.

    Returns BuildSystem or None if unknown.
    """
    p = Path(project_dir)
    if (p / "pom.xml").is_file():
        return BuildSystem.MAVEN
    elif (p / "build.gradle").is_file():
        return BuildSystem.GRADLE
    return BuildSystem.ANT


def find_all_build_files(project_dir: str) -> List[str]:
    """Find all build files that might need Jackson dependencies.
    
    Scans for:
    - pom.xml (Maven)
    - build.xml (Ant)
    - maven-build.xml (Defects4J Maven wrapper)
    - *-build.xml patterns (other build variants)
    - *.build.xml patterns (other build variants)
    
    Returns list of absolute paths to build files.
    """
    p = Path(project_dir)
    build_files = []
    
    # Standard build files
    for filename in ['pom.xml', 'build.xml', 'maven-build.xml']:
        file_path = p / filename
        if file_path.is_file():
            build_files.append(str(file_path))
    
    # Pattern-based search for other build files (limit depth to 2 levels)
    patterns = [
        '*-build.xml',
        '*.build.xml',
        'ant/build.xml'  # Common Ant build file location
    ]
    
    for pattern in patterns:
        # Search in project root and one level down
        for depth in range(3):
            search_pattern = '/'.join(['*'] * depth + [pattern])
            matches = glob.glob(str(p / search_pattern))
            build_files.extend(matches)
    
    # Remove duplicates and return
    return list(set(build_files))
