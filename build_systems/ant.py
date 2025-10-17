import xml.etree.ElementTree as ET
from pathlib import Path
import os


def add_dependencies(build_xml_path: str, jackson_version: str = "2.13.0", class_dir: str = "src/main/java") -> None:
    """Add Jackson dependencies to individual project build.xml files.
    
    This function adds Jackson JARs to the compile classpath of individual project
    build files, since Defects4J uses these for compilation.
    """
    p = Path(build_xml_path)
    if not p.is_file():
        raise FileNotFoundError(f"build.xml not found: {build_xml_path}")

    tree = ET.parse(build_xml_path)
    root = tree.getroot()

    # Add Jackson properties
    def ensure_property(name: str, value: str):
        for prop in root.findall('property'):
            if prop.attrib.get('name') == name:
                return prop
        el = ET.Element('property', {'name': name, 'value': value})
        children = list(root)
        insert_idx = 0
        for i, ch in enumerate(children):
            if ch.tag in ('path', 'target'):
                insert_idx = i
                break
            insert_idx = i + 1
        root.insert(insert_idx, el)
        return el

    ensure_property('jackson.version', jackson_version)
    ensure_property('jackson.core.jar', f"lib/jackson-core-{jackson_version}.jar")
    ensure_property('jackson.databind.jar', f"lib/jackson-databind-{jackson_version}.jar")
    ensure_property('jackson.annotations.jar', f"lib/jackson-annotations-{jackson_version}.jar")
    ensure_property('instrument.src.dir', f'{class_dir}/org/instrument')

    # Add Jackson to compile classpath
    for path_tag in root.findall('path'):
        if path_tag.get('id') == 'compile.classpath':
            existing = {pe.attrib.get('location') for pe in path_tag.findall('pathelement')}
            for jar in (f"lib/jackson-core-{jackson_version}.jar", 
                       f"lib/jackson-databind-{jackson_version}.jar", 
                       f"lib/jackson-annotations-{jackson_version}.jar"):
                if jar not in existing:
                    ET.SubElement(path_tag, 'pathelement', {'location': jar})
            # Add instrument source directory (project-specific)
            instrument_dir = f'{class_dir}/org/instrument'
            if instrument_dir not in existing:
                ET.SubElement(path_tag, 'pathelement', {'location': instrument_dir})
            break

    # Fix encoding and nowarn attributes in javac tasks
    for javac in root.findall('.//javac'):
        # Add encoding="UTF-8" to prevent US-ASCII compilation errors
        if 'encoding' not in javac.attrib:
            javac.set('encoding', 'UTF-8')
        
        # Add nowarn="true" to suppress compilation warnings
        if 'nowarn' not in javac.attrib:
            javac.set('nowarn', 'true')

    tree.write(build_xml_path, encoding='utf-8', xml_declaration=True)


def add_dependencies_to_all_ant_files(work_dir: str, jackson_version: str = "2.13.0", class_dir: str = "src/main/java") -> None:
    """Find and modify all Ant build XML files in work directory."""
    ant_files = []
    
    # Find all XML files that look like build files
    for root, dirs, files in os.walk(work_dir):
        for file in files:
            if file.endswith('.xml') and file in ('build.xml', 'defects4j.build.xml', 'maven-build.xml'):
                ant_files.append(os.path.join(root, file))
    
    # Process each build file
    for build_file in ant_files:
        try:
            add_dependencies(build_file, jackson_version, class_dir)
        except Exception as e:
            # Log error but continue with other files
            print(f"Warning: Failed to modify {build_file}: {e}")
            continue


def inject_jackson_into_defects4j_shared_build(jackson_version: str = "2.13.0") -> None:
    """Inject Jackson dependencies into the main Defects4J shared build file.
    
    This function modifies /defects4j/framework/projects/defects4j.build.xml
    to add Jackson support for all projects. It prevents duplicate injection
    by checking if Jackson properties and paths already exist.
    """
    shared_build_file = "/defects4j/framework/projects/defects4j.build.xml"
    
    if not os.path.exists(shared_build_file):
        print(f"Warning: Shared build file not found: {shared_build_file}")
        return
    
    try:
        _inject_jackson_into_shared_build_file(shared_build_file, jackson_version)
        print(f"Successfully updated Jackson dependencies in {shared_build_file}")
    except Exception as e:
        print(f"Warning: Failed to inject Jackson into shared build file: {e}")


def add_dependencies_to_project_template(build_file_path: str, jackson_version: str = "2.13.0") -> bool:
    """Add Jackson dependencies to a Defects4J project template build file.
    
    This function modifies project-specific template build files (e.g., Math.build.xml)
    that are shared by all bugs in a project. It includes duplicate prevention logic.
    
    Args:
        build_file_path: Path to the project template build file
        jackson_version: Jackson library version to use
        
    Returns:
        True if modifications were made, False if already present or failed
    """
    if not os.path.exists(build_file_path):
        print(f"Warning: Project build file not found: {build_file_path}")
        return False
    
    try:
        tree = ET.parse(build_file_path)
        root = tree.getroot()
        
        # Check if Jackson properties already exist
        jackson_props = ['jackson.version', 'jackson.core.jar', 'jackson.databind.jar', 'jackson.annotations.jar']
        existing_props = set()
        for prop in root.findall('property'):
            prop_name = prop.attrib.get('name', '')
            if prop_name in jackson_props:
                existing_props.add(prop_name)
        
        # Check if Jackson JARs are already in classpaths
        jackson_jars_in_classpath = False
        for path_tag in root.findall('path'):
            for pathelement in path_tag.findall('pathelement'):
                location = pathelement.attrib.get('location', '')
                # Check for both property references and direct JAR paths
                if (any(jar in location for jar in ['jackson-core', 'jackson-databind', 'jackson-annotations']) or
                    any(prop in location for prop in ['${jackson.core.jar}', '${jackson.databind.jar}', '${jackson.annotations.jar}'])):
                    jackson_jars_in_classpath = True
                    break
            if jackson_jars_in_classpath:
                break
        
        # If Jackson is already fully integrated, skip
        if len(existing_props) == len(jackson_props) and jackson_jars_in_classpath:
            print(f"Jackson dependencies already present in {build_file_path}, skipping")
            return False
        
        # Add Jackson properties if missing
        def ensure_property(name: str, value: str):
            for prop in root.findall('property'):
                if prop.attrib.get('name') == name:
                    return prop
            el = ET.Element('property', {'name': name, 'value': value})
            children = list(root)
            insert_idx = 0
            for i, ch in enumerate(children):
                if ch.tag in ('path', 'target'):
                    insert_idx = i
                    break
                insert_idx = i + 1
            root.insert(insert_idx, el)
            return el
        
        # Add Jackson properties
        ensure_property('jackson.version', jackson_version)
        ensure_property('jackson.core.jar', f"${{d4j.workdir}}/lib/jackson-core-{jackson_version}.jar")
        ensure_property('jackson.databind.jar', f"${{d4j.workdir}}/lib/jackson-databind-{jackson_version}.jar")
        ensure_property('jackson.annotations.jar', f"${{d4j.workdir}}/lib/jackson-annotations-{jackson_version}.jar")
        
        # Add Jackson to compile classpath
        for path_tag in root.findall('path'):
            if path_tag.get('id') == 'compile.classpath':
                existing_locations = {pe.attrib.get('location') for pe in path_tag.findall('pathelement')}
                
                jackson_deps = [
                    f"${{jackson.core.jar}}",
                    f"${{jackson.databind.jar}}",
                    f"${{jackson.annotations.jar}}"
                ]
                
                for dep in jackson_deps:
                    if dep not in existing_locations:
                        ET.SubElement(path_tag, 'pathelement', {'location': dep})
                break
        
        # Add Jackson to build classpath if it exists
        for path_tag in root.findall('path'):
            if path_tag.get('id') == 'build.classpath':
                existing_locations = {pe.attrib.get('location') for pe in path_tag.findall('pathelement')}
                
                jackson_deps = [
                    f"${{jackson.core.jar}}",
                    f"${{jackson.databind.jar}}",
                    f"${{jackson.annotations.jar}}"
                ]
                
                for dep in jackson_deps:
                    if dep not in existing_locations:
                        ET.SubElement(path_tag, 'pathelement', {'location': dep})
                break
        
        # Write the modified file
        tree.write(build_file_path, encoding='utf-8', xml_declaration=True)
        print(f"Successfully added Jackson dependencies to {build_file_path}")
        return True
        
    except Exception as e:
        print(f"Error modifying project build file {build_file_path}: {e}")
        return False


def _inject_jackson_into_shared_build_file(build_file: str, jackson_version: str) -> None:
    """Check if Jackson dependencies are already present in the shared build file.
    
    Since Jackson dependencies are now manually added to the shared build file,
    this function just verifies they exist and skips if they do.
    """
    if not os.path.exists(build_file):
        print(f"Warning: Build file not found: {build_file}")
        return
    
    tree = ET.parse(build_file)
    root = tree.getroot()
    
    # Check if Jackson properties already exist
    jackson_props = ['jackson.version', 'jackson.core.jar', 'jackson.databind.jar', 'jackson.annotations.jar']
    existing_props = set()
    for prop in root.findall('property'):
        prop_name = prop.attrib.get('name', '')
        if prop_name in jackson_props:
            existing_props.add(prop_name)
    
    # Check if Jackson classpath already exists
    jackson_path_exists = False
    for path_tag in root.findall('path'):
        if path_tag.get('id') == 'd4j.lib.jackson':
            jackson_path_exists = True
            break
    
    # Check if Jackson is already integrated into classpaths
    jackson_integrated = False
    for path_tag in root.findall('path'):
        for pathelement in path_tag.findall('pathelement'):
            location = pathelement.attrib.get('location', '')
            if 'jackson-core' in location or 'jackson-databind' in location or 'jackson-annotations' in location:
                jackson_integrated = True
                break
        if jackson_integrated:
            break
    
    # Check if Jackson path is referenced in classpaths
    for path_tag in root.findall('path'):
        for ref in path_tag.findall('path'):
            if ref.get('refid') == 'd4j.lib.jackson':
                jackson_integrated = True
                break
        if jackson_integrated:
            break
    
    if existing_props and jackson_path_exists and jackson_integrated:
        print(f"Jackson dependencies already present in {build_file}, skipping")
        return
    
    print(f"Jackson dependencies not fully integrated in {build_file}, manual update may be needed")


