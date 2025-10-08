import xml.etree.ElementTree as ET
from pathlib import Path


def add_dependencies(build_xml_path: str, jackson_version: str = "2.13.0") -> None:
    """Inject Jackson jars into Ant build.xml classpaths and properties."""
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

    def ensure_pathelems(path_el: ET.Element):
        existing = {pe.attrib.get('location') for pe in path_el.findall('pathelement')}
        for loc in ('${jackson.core.jar}', '${jackson.databind.jar}', '${jackson.annotations.jar}'):
            if loc not in existing:
                ET.SubElement(path_el, 'pathelement', {'location': loc})

    for path_tag in root.findall('path'):
        pid = (path_tag.attrib.get('id') or '').lower()
        if any(k in pid for k in ('compile', 'runtime', 'test', 'classpath')):
            ensure_pathelems(path_tag)

    tree.write(build_xml_path, encoding='utf-8', xml_declaration=True)


