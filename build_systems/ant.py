import xml.etree.ElementTree as ET
from pathlib import Path
import os


def add_dependencies(build_xml_path: str, jackson_version: str = "2.13.0") -> None:
    """Inject Jackson jars and instrument classes into Ant build.xml classpaths and properties."""
    p = Path(build_xml_path)
    if not p.is_file():
        raise FileNotFoundError(f"build.xml not found: {build_xml_path}")

    tree = ET.parse(build_xml_path)
    root = tree.getroot()

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
    ensure_property('instrument.src.dir', 'src/main/java/org/instrument')

    def ensure_pathelems(path_el: ET.Element):
        existing = {pe.attrib.get('location') for pe in path_el.findall('pathelement')}
        for loc in ('${jackson.core.jar}', '${jackson.databind.jar}', '${jackson.annotations.jar}'):
            if loc not in existing:
                ET.SubElement(path_el, 'pathelement', {'location': loc})

    def ensure_srcpath(path_el: ET.Element):
        existing = {pe.attrib.get('location') for pe in path_el.findall('pathelement')}
        if '${instrument.src.dir}' not in existing:
            ET.SubElement(path_el, 'pathelement', {'location': '${instrument.src.dir}'})

    # Add Jackson dependencies to all path elements
    for path_tag in root.findall('path'):
        pid = (path_tag.attrib.get('id') or '').lower()
        if any(k in pid for k in ('compile', 'runtime', 'test', 'classpath')):
            ensure_pathelems(path_tag)
            ensure_srcpath(path_tag)

    # Fix encoding and add Jackson to javac tasks
    for javac in root.findall('.//javac'):
        # Add encoding="UTF-8" to prevent US-ASCII compilation errors
        if 'encoding' not in javac.attrib:
            javac.set('encoding', 'UTF-8')
        
        # Add nowarn="true" to suppress compilation warnings
        if 'nowarn' not in javac.attrib:
            javac.set('nowarn', 'true')
        
        # Check if javac has inline classpath definition
        classpath = javac.find('classpath')
        if classpath is not None:
            # Check if classpath has refid attribute
            if 'refid' in classpath.attrib:
                # If it has refid, we need to modify the referenced path instead
                ref_id = classpath.attrib['refid']
                for path_tag in root.findall('path'):
                    if path_tag.get('id') == ref_id:
                        ensure_pathelems(path_tag)
                        ensure_srcpath(path_tag)
                        break
            else:
                # No refid, safe to add pathelements directly
                ensure_pathelems(classpath)
                ensure_srcpath(classpath)
        else:
            # If no inline classpath, try to reference a global path
            # Look for existing classpath reference
            classpath_ref = javac.get('classpath')
            if classpath_ref and classpath_ref.startswith('${') and classpath_ref.endswith('}'):
                # This references a global path, ensure that path has Jackson
                path_id = classpath_ref[2:-1]  # Remove ${ and }
                for path_tag in root.findall('path'):
                    if path_tag.get('id') == path_id:
                        ensure_pathelems(path_tag)
                        ensure_srcpath(path_tag)
                        break

    tree.write(build_xml_path, encoding='utf-8', xml_declaration=True)


def add_dependencies_to_all_ant_files(work_dir: str, jackson_version: str = "2.13.0") -> None:
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
            add_dependencies(build_file, jackson_version)
        except Exception as e:
            # Log error but continue with other files
            print(f"Warning: Failed to modify {build_file}: {e}")
            continue


