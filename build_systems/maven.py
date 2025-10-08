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


