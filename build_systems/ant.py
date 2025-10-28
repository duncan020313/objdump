from lxml import etree as ET
from pathlib import Path
import os
import logging
from typing import Dict, List, Callable

# Configure logger
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Helper Functions ---

def _process_build_file(build_xml_path: str, modifier_func: Callable[[ET._Element], bool]) -> bool:
    """
    Reads an XML build file, modifies it using a given function, and saves it only if changes were made.
    Uses lxml to preserve comments and formatting.

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
        # Parse with lxml to preserve comments
        parser = ET.XMLParser(remove_blank_text=False, remove_comments=False)
        tree = ET.parse(build_xml_path, parser)
        root = tree.getroot()

        if modifier_func(root):
            # Write with pretty_print to maintain formatting
            tree.write(
                build_xml_path,
                encoding='utf-8',
                xml_declaration=True,
                pretty_print=False  # Keep original formatting
            )
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


def _ensure_properties(root: ET._Element, properties: Dict[str, str]) -> bool:
    """
    Ensures that the specified properties exist in the XML root, adding them if they are missing.

    Args:
        root: The XML root element.
        properties: A dictionary of property names and values to add.

    Returns:
        True if one or more properties were added, False otherwise.
    """
    modified = False
    existing_props = {prop.get('name') for prop in root.findall('property')}

    # Find insertion point - after the last property element or before first path/target
    insert_idx = 0
    for i, child in enumerate(root):
        if child.tag == 'property':
            insert_idx = i + 1
        elif child.tag in ('path', 'target'):
            if insert_idx == 0:
                insert_idx = i
            break
    else:
        insert_idx = len(root)

    # Add missing properties with proper formatting
    for name, value in properties.items():
        if name not in existing_props:
            # Add newline and indentation before element
            if insert_idx > 0:
                prev = root[insert_idx - 1]
                if prev.tail:
                    tail = prev.tail
                else:
                    tail = "\n    "
            else:
                tail = "\n    "

            el = ET.Element('property', {'name': name, 'value': value})
            el.tail = tail
            root.insert(insert_idx, el)
            insert_idx += 1
            modified = True
    return modified


def _ensure_jackson_in_classpaths(root: ET._Element, jackson_version: str) -> bool:
    """
    Ensures that build.classpath, compile.classpath, and test.classpath all include Jackson libraries.
    Only adds to existing classpaths without creating new ones or overwriting existing elements.

    Args:
        root: The XML root element.
        jackson_version: The Jackson version to use.

    Returns:
        True if any classpath was modified, False otherwise.
    """
    modified = False

    # Target classpaths to update
    target_classpaths = ['build.classpath', 'compile.classpath', 'test.classpath']

    # Jackson JARs to add
    jackson_jars = [
        f'${{basedir}}/lib/jackson-core-{jackson_version}.jar',
        f'${{basedir}}/lib/jackson-databind-{jackson_version}.jar',
        f'${{basedir}}/lib/jackson-annotations-{jackson_version}.jar'
    ]

    # Find ALL classpath definitions (including nested ones)
    for classpath_id in target_classpaths:
        classpaths = []
        for path in root.findall('.//path'):
            if path.get('id') == classpath_id:
                classpaths.append(path)

        if len(classpaths) > 1:
            log.info(f"Found {len(classpaths)} {classpath_id} definitions, adding Jackson to all")

        # Add Jackson to all existing classpaths
        for existing_path in classpaths:
            # Skip if it's just a reference (has refid)
            if 'refid' in existing_path.attrib:
                log.info(f"Skipping {classpath_id} with refid")
                continue

            # Get existing locations
            existing_locations = {pe.get('location') for pe in existing_path.findall('pathelement')}

            # Add missing Jackson jars
            for jar in jackson_jars:
                if jar not in existing_locations:
                    el = ET.SubElement(existing_path, 'pathelement', {'location': jar})
                    el.tail = "\n        "
                    modified = True
                    log.info(f"Added {jar} to {classpath_id}")

    return modified


def _add_instrument_include_to_javac(root: ET._Element, properties: Dict[str, str]) -> bool:
    """
    Adds <include name="org/instrument/**"/> to all javac tasks in compile targets,
    adds nowarn="true" attribute, and adds Jackson library pathelement entries to javac classpaths.

    Args:
        root: The XML root element.
        properties: A dictionary of property names and values.

    Returns:
        True if any javac was modified, False otherwise.
    """
    modified = False

    # Find all targets with "compile" in name (but not "test")
    for target in root.findall('target'):
        target_name = target.get('name', '')
        if 'compile' in target_name.lower() and 'test' not in target_name.lower():
            # Find javac elements in this target
            for javac in target.findall('javac'):
                # Add nowarn="true" if not present
                if 'nowarn' not in javac.attrib:
                    javac.set('nowarn', 'true')
                    modified = True
                    log.info(f"Added nowarn='true' to javac in target '{target_name}'")

                # Add Jackson pathelement entries to classpath
                classpath = javac.find('classpath')
                if classpath is None:
                    # Create new classpath element
                    classpath = ET.Element('classpath')
                    classpath.text = '\n          '
                    classpath.tail = '\n        '
                    javac.insert(0, classpath)
                    modified = True
                    log.info(f"Created classpath in javac in target '{target_name}'")

                # Get existing pathelement locations
                existing_locations = {pe.get('location') for pe in classpath.findall('pathelement')}

                # Jackson jars to add
                jackson_jars = [
                    '${jackson.core.jar}',
                    '${jackson.databind.jar}',
                    '${jackson.annotations.jar}'
                ]

                # Add missing Jackson jars
                for jar in jackson_jars:
                    if jar not in existing_locations:
                        el = ET.SubElement(classpath, 'pathelement', {'location': jar})
                        el.tail = '\n          '
                        modified = True
                        log.info(f"Added {jar} to javac classpath in target '{target_name}'")

                # Check if org/instrument/** is already included
                existing_includes = [inc.get('name', '') for inc in javac.findall('include')]
                if 'org/instrument/**' not in existing_includes:
                    # Find last include element to insert after it
                    includes = javac.findall('include')
                    if includes:
                        last_include = includes[-1]
                        # Get the indentation from last include
                        if last_include.tail:
                            indent = '\n' + ' ' * 12  # Default indentation
                        else:
                            indent = '\n' + ' ' * 12

                        # Create new include element
                        new_include = ET.Element('include', {'name': 'org/instrument/**'})
                        new_include.tail = last_include.tail

                        # Insert after last include
                        parent = javac
                        idx = list(parent).index(last_include)
                        parent.insert(idx + 1, new_include)

                        modified = True
                        log.info(f"Added org/instrument/** include to javac in target '{target_name}'")



    # Also add nowarn and Jackson to compile.tests target
    for target in root.findall('target'):
        target_name = target.get('name', '')
        if target_name == 'compile.tests':
            for javac in target.findall('javac'):
                if 'nowarn' not in javac.attrib:
                    javac.set('nowarn', 'true')
                    modified = True
                    log.info(f"Added nowarn='true' to javac in target '{target_name}'")

                # Add Jackson pathelement entries to classpath
                classpath = javac.find('classpath')
                if classpath is None:
                    # Create new classpath element
                    classpath = ET.Element('classpath')
                    classpath.text = '\n          '
                    classpath.tail = '\n        '
                    javac.insert(0, classpath)
                    modified = True
                    log.info(f"Created classpath in javac in target '{target_name}'")

                # Get existing pathelement locations
                existing_locations = {pe.get('location') for pe in classpath.findall('pathelement')}

                # Jackson jars to add
                jackson_jars = [
                    '${jackson.core.jar}',
                    '${jackson.databind.jar}',
                    '${jackson.annotations.jar}'
                ]

                # Add missing Jackson jars
                for jar in jackson_jars:
                    if jar not in existing_locations:
                        el = ET.SubElement(classpath, 'pathelement', {'location': jar})
                        el.tail = '\n          '
                        modified = True
                        log.info(f"Added {jar} to javac classpath in target '{target_name}'")

    return modified


def _add_jackson_to_path_filesets(root: ET._Element) -> bool:
    """
    Adds Jackson jar includes to fileset elements within path definitions.
    Creates a new fileset with Jackson jars from d4j.workdir/lib if not already present.

    Args:
        root: The XML root element.

    Returns:
        True if any path was modified, False otherwise.
    """
    modified = False

    # Jackson jars to add
    jackson_jars = [
        'jackson-core-*.jar',
        'jackson-databind-*.jar',
        'jackson-annotations-*.jar'
    ]

    # Find all path elements
    for path_elem in root.findall('.//path'):
        path_id = path_elem.get('id', '')

        # Skip if it's just a reference (has refid)
        if 'refid' in path_elem.attrib:
            continue

        # Check if Jackson jars are already included in any fileset
        has_jackson = False
        for fileset in path_elem.findall('fileset'):
            fileset_dir = fileset.get('dir', '')
            if '${d4j.workdir}/lib' in fileset_dir or '${d4j.home}/lib' in fileset_dir:
                # Check if Jackson includes exist
                includes = [inc.get('name', '') for inc in fileset.findall('include')]
                if any('jackson' in inc for inc in includes):
                    has_jackson = True
                    break

        if not has_jackson:
            # Add new fileset with Jackson jars
            # Find last fileset to insert after it
            filesets = path_elem.findall('fileset')

            # Create new fileset element
            new_fileset = ET.Element('fileset', {'dir': '${d4j.workdir}/lib'})

            # Add Jackson jar includes
            for jar in jackson_jars:
                include_elem = ET.Element('include', {'name': jar})
                include_elem.tail = '\n      '
                new_fileset.append(include_elem)

            # Set proper indentation
            new_fileset.text = '\n      '
            new_fileset.tail = '\n  '

            # Insert after last fileset or at the end
            if filesets:
                last_fileset = filesets[-1]
                idx = list(path_elem).index(last_fileset)
                path_elem.insert(idx + 1, new_fileset)
            else:
                path_elem.append(new_fileset)

            modified = True
            log.info(f"Added Jackson fileset to path '{path_id}'")

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
    def modifier(root: ET._Element) -> bool:
        properties = {
            'jackson.version': jackson_version,
            'jackson.core.jar': f"${{d4j.workdir}}/lib/jackson-core-{jackson_version}.jar",
            'jackson.databind.jar': f"${{d4j.workdir}}/lib/jackson-databind-{jackson_version}.jar",
            'jackson.annotations.jar': f"${{d4j.workdir}}/lib/jackson-annotations-{jackson_version}.jar",
            'instrument.src.dir': f'{class_dir}/org/instrument'
        }
        if "jacksoncore" in build_xml_path.lower():
            del properties['jackson.core.jar']

        modified1 = _ensure_properties(root, properties)
        modified2 = _ensure_jackson_in_classpaths(root, jackson_version)
        prohibited = ["math", "jsoup", "compress", "mockito", "closure", "time", "cli", "lang"]
        if not any(p in build_xml_path.lower() for p in prohibited):
            modified3 = _add_instrument_include_to_javac(root, properties)
        else:
            modified3 = False
        modified4 = _add_jackson_to_path_filesets(root)

        return modified1 or modified2 or modified3 or modified4

    return _process_build_file(build_xml_path, modifier)


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
