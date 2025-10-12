import xml.etree.ElementTree as ET
from pathlib import Path


POM_NS = 'http://maven.apache.org/POM/4.0.0'
NS = {'m': POM_NS}


def add_dependencies(pom_path: str, jackson_version: str = "2.13.0") -> None:
    """Add Jackson core/artifacts into pom.xml if missing."""
    p = Path(pom_path)
    if not p.is_file():
        raise FileNotFoundError(f"pom.xml not found: {pom_path}")

    ET.register_namespace('', POM_NS)
    tree = ET.parse(pom_path)
    root = tree.getroot()

    # properties
    properties = root.find('m:properties', NS)
    if properties is None:
        properties = ET.SubElement(root, f'{{{POM_NS}}}properties')
    if properties.find(f'm:jackson.version', NS) is None:
        jv = ET.SubElement(properties, f'{{{POM_NS}}}jackson.version')
        jv.text = jackson_version

    # dependencies
    deps = root.find('m:dependencies', NS)
    if deps is None:
        deps = ET.SubElement(root, f'{{{POM_NS}}}dependencies')

    def ensure(group_id: str, artifact_id: str) -> None:
        for dep in deps.findall('m:dependency', NS):
            gid = dep.find('m:groupId', NS)
            aid = dep.find('m:artifactId', NS)
            if gid is not None and aid is not None and gid.text == group_id and aid.text == artifact_id:
                return
        dep = ET.SubElement(deps, f'{{{POM_NS}}}dependency')
        gid = ET.SubElement(dep, f'{{{POM_NS}}}groupId')
        gid.text = group_id
        aid = ET.SubElement(dep, f'{{{POM_NS}}}artifactId')
        aid.text = artifact_id
        ver = ET.SubElement(dep, f'{{{POM_NS}}}version')
        ver.text = '${jackson.version}'

    ensure('com.fasterxml.jackson.core', 'jackson-core')
    ensure('com.fasterxml.jackson.core', 'jackson-annotations')
    ensure('com.fasterxml.jackson.core', 'jackson-databind')

    tree.write(pom_path, encoding='utf-8', xml_declaration=True)


def add_dependencies_to_maven_build_xml(maven_build_xml_path: str, jackson_version: str = "2.13.0") -> None:
    """Add Jackson jars into maven-build.xml classpaths and properties (Ant-style)."""
    p = Path(maven_build_xml_path)
    if not p.is_file():
        raise FileNotFoundError(f"maven-build.xml not found: {maven_build_xml_path}")

    tree = ET.parse(maven_build_xml_path)
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

    tree.write(maven_build_xml_path, encoding='utf-8', xml_declaration=True)


