from pathlib import Path
from typing import Optional, List
import glob
import os
import xml.etree.ElementTree as ET

from jt_types import BuildSystem


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


def fix_encoding_in_build_files(work_dir: str) -> None:
    """Ensure all javac tasks use UTF-8 encoding to prevent US-ASCII compilation errors.
    
    This function scans all XML build files in the work directory and adds
    encoding="UTF-8" to any <javac> elements that don't already have an encoding attribute.
    """
    build_files = find_all_build_files(work_dir)
    
    for build_file in build_files:
        try:
            tree = ET.parse(build_file)
            root = tree.getroot()
            
            # Find all javac elements and add encoding if missing
            modified = False
            for javac in root.findall('.//javac'):
                if 'encoding' not in javac.attrib:
                    javac.set('encoding', 'UTF-8')
                    modified = True
                
                # Add nowarn="true" to suppress compilation warnings
                if 'nowarn' not in javac.attrib:
                    javac.set('nowarn', 'true')
                    modified = True
            
            # Write back if modified
            if modified:
                tree.write(build_file, encoding='utf-8', xml_declaration=True)
                
        except Exception as e:
            # Log error but continue with other files
            print(f"Warning: Failed to fix encoding in {build_file}: {e}")
            continue


def inject_jackson_into_all_build_files(work_dir: str, jackson_version: str = "2.13.0") -> None:
    """Find and modify all build XML files in work directory to include Jackson dependencies.
    
    This function:
    1. Finds all build XML files (build.xml, defects4j.build.xml, maven-build.xml, etc.)
    2. Applies appropriate Jackson dependency injection based on file type
    3. Handles both Ant-style and Maven-style build files
    """
    from .ant import add_dependencies_to_all_ant_files
    from .maven import add_dependencies_to_maven_build_xml
    
    # Find all build files
    build_files = find_all_build_files(work_dir)
    
    for build_file in build_files:
        try:
            filename = os.path.basename(build_file)
            
            if filename == 'pom.xml':
                # Handle Maven POM files
                from .maven import add_dependencies
                add_dependencies(build_file, jackson_version)
            elif filename in ('maven-build.xml', 'defects4j.build.xml') or filename.endswith('-build.xml'):
                # Handle Maven-generated Ant build files
                add_dependencies_to_maven_build_xml(build_file, jackson_version)
            elif filename == 'build.xml' or filename.endswith('.build.xml'):
                # Handle standard Ant build files
                from .ant import add_dependencies
                add_dependencies(build_file, jackson_version)
                
        except Exception as e:
            # Log error but continue with other files
            print(f"Warning: Failed to inject Jackson into {build_file}: {e}")
            continue


