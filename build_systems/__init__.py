from pathlib import Path
from typing import Optional, List
import glob
import os
import xml.etree.ElementTree as ET
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
            log.warning(f"Failed to fix encoding in {build_file}: {e}")
            continue


def inject_jackson_into_all_build_files(work_dir: str, jackson_version: str = "2.13.0") -> None:
    """Find and modify Maven build files in work directory to include Jackson dependencies.
    
    Ant projects now use the centralized Defects4J shared build file for Jackson dependencies,
    so this function only handles Maven POM files.
    """
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
            # Ant build files (build.xml) are now handled by the shared Defects4J build file
                
        except Exception as e:
            # Log error but continue with other files
            log.warning(f"Failed to inject Jackson into {build_file}: {e}")
            continue


def inject_jackson_into_project_templates(project_ids: List[str], jackson_version: str = "2.13.0") -> None:
    """Inject Jackson dependencies into Defects4J project template build files.
    
    This function modifies project-specific template build files (e.g., Math.build.xml)
    that are shared by all bugs in each project. It uses defects4j info to get the
    correct build file path for each project.
    
    Args:
        project_ids: List of Defects4J project IDs (e.g., ["Math", "Lang", "Chart"])
        jackson_version: Jackson library version to use
    """
    from .ant import add_dependencies_to_project_template
    from defects4j import get_project_build_file
    
    modified_count = 0
    skipped_count = 0
    failed_count = 0
    
    for project_id in project_ids:
        log.info(f"Processing project template for {project_id}...")
        
        # Get the project's build file path using defects4j info
        build_file_path = get_project_build_file(project_id)
        if not build_file_path:
            log.warning(f"Could not get build file path for project {project_id}")
            failed_count += 1
            continue
        
        # Add Jackson dependencies to the project template
        success = add_dependencies_to_project_template(build_file_path, jackson_version)
        if success:
            modified_count += 1
        else:
            # Check if it was skipped due to already present
            if "already present" in str(success) or success is False:
                skipped_count += 1
            else:
                failed_count += 1
    
    log.info(f"Project template injection completed:")
    log.info(f"  - Modified: {modified_count}")
    log.info(f"  - Skipped (already present): {skipped_count}")
    log.info(f"  - Failed: {failed_count}")


def inject_jackson_into_defects4j_shared_build(jackson_version: str = "2.13.0") -> None:
    """Inject Jackson dependencies into all Defects4J shared project build files.
    
    This function modifies the shared build files in /defects4j/framework/projects/
    that are used by all bugs of each project. It prevents duplicate injection
    by checking if Jackson properties and paths already exist.
    """
    from .ant import inject_jackson_into_defects4j_shared_build as _inject_shared
    _inject_shared(jackson_version)


