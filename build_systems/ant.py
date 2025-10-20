import xml.etree.ElementTree as ET
from pathlib import Path
import os
import logging
from typing import Dict, List, Callable

# Configure logger
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Helper Functions ---

def _process_build_file(build_xml_path: str, modifier_func: Callable[[ET.Element], bool]) -> bool:
    """
    Reads an XML build file, modifies it using a given function, and saves it only if changes were made.

    Args:
        build_xml_path: Path to the build file.
        modifier_func: A function that takes the XML root element and performs modifications.
                       It should return True if modifications were made, False otherwise.

    Returns:
        True if the file was successfully modified, False otherwise.
    """
    p = Path(build_xml_path)
    if not p.is_file():
        log.error(f"Build file not found: {build_xml_path}")
        return False

    try:
        tree = ET.parse(build_xml_path)
        root = tree.getroot()

        if modifier_func(root):
            # Write the file with utf-8 encoding and XML declaration.
            tree.write(build_xml_path, encoding='utf-8', xml_declaration=True)
            log.info(f"Successfully modified file: {build_xml_path}")
            return True
        else:
            log.info(f"No changes needed, file is already up-to-date: {build_xml_path}")
            return False
    except ET.ParseError as e:
        log.error(f"XML parsing error in {build_xml_path}: {e}")
        return False
    except Exception as e:
        log.error(f"Error modifying file {build_xml_path}: {e}")
        return False

def _ensure_properties(root: ET.Element, properties: Dict[str, str]) -> bool:
    """
    Ensures that the specified properties exist in the XML root, adding them if they are missing.

    Args:
        root: The XML root element.
        properties: A dictionary of property names and values to add.

    Returns:
        True if one or more properties were added, False otherwise.
    """
    modified = False
    existing_props = {prop.attrib.get('name') for prop in root.findall('property')}
    
    # Calculate insertion index (before the first 'path' or 'target' tag)
    insert_idx = len(list(root))
    for i, child in enumerate(root):
        if child.tag in ('path', 'target'):
            insert_idx = i
            break
            
    for name, value in reversed(properties.items()): # Insert in reverse to maintain order
        if name not in existing_props:
            el = ET.Element('property', {'name': name, 'value': value})
            root.insert(insert_idx, el)
            modified = True
    return modified

def _add_pathelements_to_classpath(root: ET.Element, classpath_id: str, locations: List[str]) -> bool:
    """
    Adds pathelements to a classpath with a specified ID.

    Args:
        root: The XML root element.
        classpath_id: The id of the target <path> tag.
        locations: A list of location attribute values for the pathelements to add.

    Returns:
        True if one or more pathelements were added, False otherwise.
    """
    modified = False
    for path_tag in root.findall('path'):
        if path_tag.get('id') == classpath_id:
            if 'refid' in path_tag.attrib:
                log.warning(f"Path '{classpath_id}' has a refid attribute, cannot add dependencies directly.")
                return False
            
            existing_locations = {pe.attrib.get('location') for pe in path_tag.findall('pathelement')}
            for loc in locations:
                if loc not in existing_locations:
                    ET.SubElement(path_tag, 'pathelement', {'location': loc})
                    modified = True
            break # Found the correct path ID, so exit loop
    return modified

def _update_javac_tasks(root: ET.Element) -> bool:
    """
    Adds `encoding='UTF-8'` and `nowarn='true'` attributes to all javac tasks.

    Args:
        root: The XML root element.

    Returns:
        True if one or more javac tasks were modified, False otherwise.
    """
    modified = False
    for javac in root.findall('.//javac'):
        if 'encoding' not in javac.attrib:
            javac.set('encoding', 'UTF-8')
            modified = True
        if 'nowarn' not in javac.attrib:
            javac.set('nowarn', 'true')
            modified = True
    return modified

def _fix_compile_target_javac(root: ET.Element) -> bool:
    """
    Fixes javac tasks in compile targets to use compile.classpath and include instrumentation sources.
    
    This function:
    1. Finds compile-related targets (name contains "compile" but not "test")
    2. Updates javac classpath refid from "build.classpath" to "compile.classpath"
    3. Adds <include name="org/instrument/**" /> if not present
    
    Args:
        root: The XML root element.
        
    Returns:
        True if one or more javac tasks were modified, False otherwise.
    """
    modified = False
    
    # Find all targets that are compile-related (contain "compile" but not "test")
    for target in root.findall('target'):
        target_name = target.get('name', '')
        if 'compile' in target_name.lower() and 'test' not in target_name.lower():
            # Find javac tasks within this compile target
            for javac in target.findall('javac'):
                # Check if javac has a classpath element
                classpath = javac.find('classpath')
                if classpath is not None:
                    # Check if it references build.classpath
                    refid = classpath.get('refid')
                    if refid == 'build.classpath':
                        # Change to compile.classpath
                        classpath.set('refid', 'compile.classpath')
                        modified = True
                        log.info(f"Updated classpath refid from build.classpath to compile.classpath in target '{target_name}'")
                
                # Check if org/instrument/** is already included
                existing_includes = [inc.get('name', '') for inc in javac.findall('include')]
                if 'org/instrument/**' not in existing_includes:
                    # Add the instrumentation include
                    include_elem = ET.SubElement(javac, 'include')
                    include_elem.set('name', 'org/instrument/**')
                    modified = True
                    log.info(f"Added org/instrument/** include to javac in target '{target_name}'")
    
    return modified

# --- Main Functions ---

def add_jackson_to_build_file(build_xml_path: str, jackson_version: str = "2.13.0", class_dir: str = "src/main/java") -> bool:
    """
    Adds Jackson dependencies to an individual Ant build file (build.xml) and updates javac tasks.

    Args:
        build_xml_path: Path to the build.xml file to modify.
        jackson_version: The Jackson version to use.
        class_dir: The path to the class directory.

    Returns:
        True if the file was successfully modified.
    """
    def modifier(root: ET.Element) -> bool:
        properties = {
            'jackson.version': jackson_version,
            'jackson.core.jar': f"lib/jackson-core-{jackson_version}.jar",
            'jackson.databind.jar': f"lib/jackson-databind-{jackson_version}.jar",
            'jackson.annotations.jar': f"lib/jackson-annotations-{jackson_version}.jar",
            'instrument.src.dir': f'{class_dir}/org/instrument'
        }
        
        classpath_locations = [
            f"lib/jackson-core-{jackson_version}.jar",
            f"lib/jackson-databind-{jackson_version}.jar",
            f"lib/jackson-annotations-{jackson_version}.jar",
            f'{class_dir}/org/instrument'
        ]

        # Call each modification function and combine results with OR
        modified1 = _ensure_properties(root, properties)
        modified2 = _add_pathelements_to_classpath(root, 'compile.classpath', classpath_locations)
        modified3 = _update_javac_tasks(root)
        
        return modified1 or modified2 or modified3

    return _process_build_file(build_xml_path, modifier)


def add_jackson_to_project_template(build_file_path: str, jackson_version: str = "2.13.0") -> bool:
    """
    Adds Jackson dependencies to a Defects4J project template build file.
    (e.g., /path/to/d4j/project/Chart.build.xml)

    Args:
        build_file_path: Path to the project template build file.
        jackson_version: The Jackson version to use.

    Returns:
        True if the file was successfully modified.
    """
    def modifier(root: ET.Element) -> bool:
        properties = {
            'jackson.version': jackson_version,
            'jackson.core.jar': f"${{d4j.workdir}}/lib/jackson-core-{jackson_version}.jar",
            'jackson.databind.jar': f"${{d4j.workdir}}/lib/jackson-databind-{jackson_version}.jar",
            'jackson.annotations.jar': f"${{d4j.workdir}}/lib/jackson-annotations-{jackson_version}.jar"
        }
        
        classpath_locations = [
            "${jackson.core.jar}",
            "${jackson.databind.jar}",
            "${jackson.annotations.jar}"
        ]

        modified1 = _ensure_properties(root, properties)
        # Attempt to add to both compile.classpath and build.classpath
        modified2 = _add_pathelements_to_classpath(root, 'compile.classpath', classpath_locations)
        modified3 = _add_pathelements_to_classpath(root, 'build.classpath', classpath_locations)
        
        # NEW: Fix javac tasks in compile targets to use compile.classpath and include instrumentation sources
        modified4 = _fix_compile_target_javac(root)
        
        return modified1 or modified2 or modified3 or modified4

    return _process_build_file(build_file_path, modifier)


def process_all_ant_files_in_dir(work_dir: str, jackson_version: str = "2.13.0", class_dir: str = "src/main/java") -> None:
    """
    Finds and adds Jackson dependencies to all Ant build files within a working directory.

    Args:
        work_dir: The working directory to start searching from.
        jackson_version: The Jackson version to use.
        class_dir: The path to the class directory.
    """
    for root_dir, _, files in os.walk(work_dir):
        for file in files:
            if file in ('build.xml', 'defects4j.build.xml', 'maven-build.xml'):
                build_file = os.path.join(root_dir, file)
                log.info(f"Processing file: {build_file}")
                add_jackson_to_build_file(build_file, jackson_version, class_dir)


def verify_jackson_in_defects4j_shared_build(jackson_version: str = "2.13.0") -> None:
    """
    Verifies that Jackson dependencies are correctly configured in the Defects4J shared build file.
    This function now focuses on verification rather than modification.
    """
    shared_build_file = "/defects4j/framework/projects/defects4j.build.xml"
    if not os.path.exists(shared_build_file):
        log.warning(f"Shared build file not found: {shared_build_file}")
        return

    try:
        tree = ET.parse(shared_build_file)
        root = tree.getroot()

        # Check for existence of Jackson properties
        expected_props = {'jackson.version', 'jackson.core.jar', 'jackson.databind.jar', 'jackson.annotations.jar'}
        existing_props = {prop.attrib.get('name') for prop in root.findall('property')}
        
        if not expected_props.issubset(existing_props):
            log.warning(f"Jackson properties are not fully configured in {shared_build_file}. Manual verification may be needed.")
            return

        # Check for existence of the Jackson library path
        if not any(path.get('id') == 'd4j.lib.jackson' for path in root.findall('path')):
            log.warning(f"Path 'd4j.lib.jackson' is not defined in {shared_build_file}. Manual verification may be needed.")
            return
        
        log.info(f"Jackson dependencies appear to be correctly configured in {shared_build_file}.")

    except Exception as e:
        log.error(f"Error verifying shared build file: {e}")