import xml.etree.ElementTree as ET
import subprocess
import logging
from pathlib import Path
from typing import Optional


log = logging.getLogger(__name__)

POM_NS = 'http://maven.apache.org/POM/4.0.0'
NS = {'m': POM_NS}


def setup_jackson_dependencies(workdir: str, jackson_version: str = "2.13.0") -> None:
    """
    Setup Jackson dependencies for a Maven project.
    
    This function:
    1. Adds Jackson dependencies to pom.xml
    2. Adds Jackson to maven-build.xml (if exists, for Defects4J projects)
    3. Downloads Jackson JARs using mvn dependency:copy-dependencies
    
    Args:
        workdir: Working directory containing the Maven project
        jackson_version: Jackson version to install (default: 2.13.0)
    """
    workdir_path = Path(workdir)
    if not workdir_path.is_dir():
        raise ValueError(f"workdir does not exist: {workdir}")
    
    pom_path = workdir_path / "pom.xml"
    if not pom_path.is_file():
        log.warning(f"pom.xml not found in {workdir}, skipping Maven setup")
        return
    
    # Step 1: Add Jackson to pom.xml
    log.info(f"Adding Jackson {jackson_version} to {pom_path}")
    add_jackson_to_pom(str(pom_path), jackson_version)
    
    # Step 2: Add Jackson to maven-build.xml if it exists (Defects4J projects)
    maven_build_xml = workdir_path / "maven-build.xml"
    if maven_build_xml.is_file():
        log.info(f"Adding Jackson to {maven_build_xml}")
        add_jackson_to_maven_build_xml(str(maven_build_xml), jackson_version)
    
    # Step 3: Download Jackson JARs using Maven
    log.info(f"Downloading Jackson JARs to {workdir}/lib")
    download_jackson_jars_with_maven(workdir)


def add_jackson_to_pom(pom_path: str, jackson_version: str = "2.13.0") -> None:
    """
    Add Jackson dependencies to pom.xml.
    
    Args:
        pom_path: Path to pom.xml file
        jackson_version: Jackson version to add
    """
    pom_file = Path(pom_path)
    if not pom_file.is_file():
        raise FileNotFoundError(f"pom.xml not found: {pom_path}")
    
    ET.register_namespace('', POM_NS)
    tree = ET.parse(pom_path)
    root = tree.getroot()
    
    # Add or update properties section
    properties = root.find('m:properties', NS)
    if properties is None:
        # Insert properties after artifactId if it exists
        insert_index = 0
        for i, child in enumerate(root):
            if child.tag.endswith('artifactId'):
                insert_index = i + 1
                break
        properties = ET.Element(f'{{{POM_NS}}}properties')
        root.insert(insert_index, properties)
    
    # Add jackson.version property if not exists
    if properties.find('m:jackson.version', NS) is None:
        jackson_ver_prop = ET.SubElement(properties, f'{{{POM_NS}}}jackson.version')
        jackson_ver_prop.text = jackson_version
    
    # Add or update dependencies section
    dependencies = root.find('m:dependencies', NS)
    if dependencies is None:
        dependencies = ET.SubElement(root, f'{{{POM_NS}}}dependencies')
    
    # Helper to ensure a dependency exists
    def ensure_dependency(group_id: str, artifact_id: str) -> None:
        for dep in dependencies.findall('m:dependency', NS):
            gid = dep.find('m:groupId', NS)
            aid = dep.find('m:artifactId', NS)
            if gid is not None and aid is not None:
                if gid.text == group_id and aid.text == artifact_id:
                    return
        
        # Add new dependency
        dep = ET.SubElement(dependencies, f'{{{POM_NS}}}dependency')
        gid = ET.SubElement(dep, f'{{{POM_NS}}}groupId')
        gid.text = group_id
        aid = ET.SubElement(dep, f'{{{POM_NS}}}artifactId')
        aid.text = artifact_id
        ver = ET.SubElement(dep, f'{{{POM_NS}}}version')
        ver.text = '${jackson.version}'
    
    # Add Jackson dependencies
    ensure_dependency('com.fasterxml.jackson.core', 'jackson-core')
    ensure_dependency('com.fasterxml.jackson.core', 'jackson-databind')
    ensure_dependency('com.fasterxml.jackson.core', 'jackson-annotations')
    
    tree.write(pom_path, encoding='utf-8', xml_declaration=True)


def add_jackson_to_maven_build_xml(build_xml_path: str, jackson_version: str = "2.13.0") -> None:
    """
    Add Jackson to maven-build.xml (Ant-style build file used by Defects4J).
    
    Args:
        build_xml_path: Path to maven-build.xml file
        jackson_version: Jackson version
    """
    build_file = Path(build_xml_path)
    if not build_file.is_file():
        raise FileNotFoundError(f"maven-build.xml not found: {build_xml_path}")
    
    tree = ET.parse(build_xml_path)
    root = tree.getroot()
    
    # Add properties
    def ensure_property(name: str, value: str) -> None:
        for prop in root.findall('property'):
            if prop.attrib.get('name') == name:
                return
        
        # Find insertion point (before first path or target element)
        insert_idx = len(list(root))
        for i, child in enumerate(root):
            if child.tag in ('path', 'target'):
                insert_idx = i
                break
        
        prop_elem = ET.Element('property', {'name': name, 'value': value})
        root.insert(insert_idx, prop_elem)
    
    ensure_property('jackson.version', jackson_version)
    ensure_property('jackson.core.jar', f'lib/jackson-core-{jackson_version}.jar')
    ensure_property('jackson.databind.jar', f'lib/jackson-databind-{jackson_version}.jar')
    ensure_property('jackson.annotations.jar', f'lib/jackson-annotations-{jackson_version}.jar')
    ensure_property('instrument.src.dir', 'src/main/java/org/instrument')
    
    # Add Jackson JARs to classpath elements
    def ensure_jackson_in_path(path_elem: ET.Element) -> None:
        existing_locations = {pe.attrib.get('location') for pe in path_elem.findall('pathelement')}
        
        jackson_jars = [
            '${jackson.core.jar}',
            '${jackson.databind.jar}',
            '${jackson.annotations.jar}'
        ]
        
        for jar in jackson_jars:
            if jar not in existing_locations:
                ET.SubElement(path_elem, 'pathelement', {'location': jar})
    
    def ensure_instrument_srcpath(path_elem: ET.Element) -> None:
        existing_locations = {pe.attrib.get('location') for pe in path_elem.findall('pathelement')}
        if '${instrument.src.dir}' not in existing_locations:
            ET.SubElement(path_elem, 'pathelement', {'location': '${instrument.src.dir}'})
    
    # Add to all relevant path elements
    for path_elem in root.findall('path'):
        path_id = (path_elem.attrib.get('id') or '').lower()
        if any(keyword in path_id for keyword in ('compile', 'runtime', 'test', 'classpath')):
            ensure_jackson_in_path(path_elem)
            ensure_instrument_srcpath(path_elem)
    
    # Fix javac tasks
    for javac in root.findall('.//javac'):
        # Add encoding
        if 'encoding' not in javac.attrib:
            javac.set('encoding', 'UTF-8')
        
        # Add nowarn
        if 'nowarn' not in javac.attrib:
            javac.set('nowarn', 'true')
        
        # Handle classpath
        classpath = javac.find('classpath')
        if classpath is not None:
            if 'refid' in classpath.attrib:
                # Referenced classpath - ensure the referenced path has Jackson
                ref_id = classpath.attrib['refid']
                for path_elem in root.findall('path'):
                    if path_elem.get('id') == ref_id:
                        ensure_jackson_in_path(path_elem)
                        ensure_instrument_srcpath(path_elem)
                        break
            else:
                # Inline classpath
                ensure_jackson_in_path(classpath)
                ensure_instrument_srcpath(classpath)
    
    tree.write(build_xml_path, encoding='utf-8', xml_declaration=True)


def download_jackson_jars_with_maven(workdir: str) -> None:
    """
    Download Jackson JARs using Maven dependency plugin.
    
    Args:
        workdir: Working directory containing pom.xml
    """
    workdir_path = Path(workdir)
    lib_dir = workdir_path / 'lib'
    lib_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        'mvn',
        'dependency:copy-dependencies',
        f'-DoutputDirectory=lib',
        '-DincludeGroupIds=com.fasterxml.jackson.core',
        '-DincludeArtifactIds=jackson-core,jackson-databind,jackson-annotations'
    ]
    
    try:
        log.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            log.error(f"Maven command failed with return code {result.returncode}")
            log.error(f"stdout: {result.stdout}")
            log.error(f"stderr: {result.stderr}")
            raise RuntimeError(f"Failed to download Jackson JARs: {result.stderr}")
        
        log.info("Jackson JARs downloaded successfully")
        if result.stdout:
            log.debug(f"Maven output: {result.stdout}")
            
    except subprocess.TimeoutExpired:
        log.error("Maven command timed out after 120 seconds")
        raise
    except FileNotFoundError:
        log.error("Maven (mvn) command not found. Please install Maven.")
        raise
