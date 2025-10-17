import xml.etree.ElementTree as ET
from pathlib import Path
import os


def add_dependencies(build_xml_path: str, jackson_version: str = "2.13.0", class_dir: str = "src/main/java") -> None:
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
    ensure_property('instrument.src.dir', f'{class_dir}/org/instrument')

    def ensure_pathelems(path_el: ET.Element):
        existing = {pe.attrib.get('location') for pe in path_el.findall('pathelement')}
        for loc in ('${jackson.core.jar}', '${jackson.databind.jar}', '${jackson.annotations.jar}'):
            if loc not in existing:
                ET.SubElement(path_el, 'pathelement', {'location': loc})
        
        # Also add direct JAR file paths as fallback
        jar_files = [
            f"lib/jackson-core-{jackson_version}.jar",
            f"lib/jackson-databind-{jackson_version}.jar", 
            f"lib/jackson-annotations-{jackson_version}.jar"
        ]
        for jar_file in jar_files:
            if jar_file not in existing:
                ET.SubElement(path_el, 'pathelement', {'location': jar_file})

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
            
            # If still no classpath found, create one with Jackson dependencies
            if classpath is None and not classpath_ref:
                classpath = ET.SubElement(javac, 'classpath')
                ensure_pathelems(classpath)
                ensure_srcpath(classpath)

    # Add Jackson to junit tasks
    for junit in root.findall('.//junit'):
        # Check if junit has inline classpath definition
        classpath = junit.find('classpath')
        if classpath is not None:
            # Check if classpath has refid attribute
            if 'refid' in classpath.attrib:
                # Modify the referenced path
                ref_id = classpath.attrib['refid']
                for path_tag in root.findall('path'):
                    if path_tag.get('id') == ref_id:
                        ensure_pathelems(path_tag)
                        ensure_srcpath(path_tag)
                        break
            else:
                # No refid, add pathelements directly
                ensure_pathelems(classpath)
                ensure_srcpath(classpath)
        else:
            # If no inline classpath, check for classpath reference
            classpath_ref = junit.get('classpath')
            if classpath_ref and classpath_ref.startswith('${') and classpath_ref.endswith('}'):
                # This references a global path
                path_id = classpath_ref[2:-1]
                for path_tag in root.findall('path'):
                    if path_tag.get('id') == path_id:
                        ensure_pathelems(path_tag)
                        ensure_srcpath(path_tag)
                        break

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
    """Inject Jackson dependencies into all Defects4J shared project build files.
    
    This function modifies the shared build files in /defects4j/framework/projects/
    that are used by all bugs of each project. It prevents duplicate injection
    by checking if Jackson properties and paths already exist.
    """
    import subprocess
    import xml.etree.ElementTree as ET
    
    try:
        # Get all Defects4J project IDs
        result = subprocess.run(['defects4j', 'pids'], capture_output=True, text=True, check=True)
        project_ids = [pid.strip() for pid in result.stdout.strip().split('\n') if pid.strip()]
        
        # Get unique build file paths for each project
        build_files = set()
        for pid in project_ids:
            try:
                result = subprocess.run(['defects4j', 'query', '-p', pid, '-q', 'project.build.file'], 
                                      capture_output=True, text=True, check=True)
                # Get the first line (all bugs use the same build file)
                first_line = result.stdout.strip().split('\n')[0]
                if ',' in first_line:
                    build_file = first_line.split(',')[1].strip()
                    build_files.add(build_file)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to query build file for project {pid}: {e}")
                continue
        
        # Process each unique build file
        for build_file in build_files:
            try:
                _inject_jackson_into_shared_build_file(build_file, jackson_version)
            except Exception as e:
                print(f"Warning: Failed to inject Jackson into {build_file}: {e}")
                continue
                
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to get Defects4J project IDs: {e}")
    except Exception as e:
        print(f"Warning: Failed to inject Jackson into Defects4J shared build files: {e}")


def _inject_jackson_into_shared_build_file(build_file: str, jackson_version: str) -> None:
    """Inject Jackson dependencies into a single Defects4J shared build file with duplicate prevention."""
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
    
    # Check if Jackson JARs already exist in any classpath
    existing_jars = set()
    for path_tag in root.findall('path'):
        for pathelement in path_tag.findall('pathelement'):
            location = pathelement.attrib.get('location', '')
            if 'jackson-core' in location or 'jackson-databind' in location or 'jackson-annotations' in location:
                existing_jars.add(location)
    
    # Only inject if Jackson dependencies are not already present
    if existing_props or existing_jars:
        print(f"Jackson dependencies already present in {build_file}, skipping")
        return
    
    print(f"Injecting Jackson dependencies into {build_file}")
    
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
    ensure_property('instrument.src.dir', 'src/main/java/org/instrument')
    
    # Add Jackson JARs to classpaths
    def ensure_pathelems(path_el: ET.Element):
        existing = {pe.attrib.get('location') for pe in path_el.findall('pathelement')}
        for loc in ('${jackson.core.jar}', '${jackson.databind.jar}', '${jackson.annotations.jar}'):
            if loc not in existing:
                ET.SubElement(path_el, 'pathelement', {'location': loc})
    
    def ensure_srcpath(path_el: ET.Element):
        existing = {pe.attrib.get('location') for pe in path_el.findall('pathelement')}
        if '${instrument.src.dir}' not in existing:
            ET.SubElement(path_el, 'pathelement', {'location': '${instrument.src.dir}'})
    
    # Add Jackson dependencies to relevant path elements
    for path_tag in root.findall('path'):
        pid = (path_tag.attrib.get('id') or '').lower()
        if any(k in pid for k in ('compile', 'runtime', 'test', 'classpath', 'd4j')):
            ensure_pathelems(path_tag)
            ensure_srcpath(path_tag)
    
    # Add Jackson to javac tasks
    for javac in root.findall('.//javac'):
        if 'encoding' not in javac.attrib:
            javac.set('encoding', 'UTF-8')
        if 'nowarn' not in javac.attrib:
            javac.set('nowarn', 'true')
        
        classpath = javac.find('classpath')
        if classpath is not None:
            if 'refid' in classpath.attrib:
                ref_id = classpath.attrib['refid']
                for path_tag in root.findall('path'):
                    if path_tag.get('id') == ref_id:
                        ensure_pathelems(path_tag)
                        ensure_srcpath(path_tag)
                        break
            else:
                ensure_pathelems(classpath)
                ensure_srcpath(classpath)
        else:
            classpath_ref = javac.get('classpath')
            if classpath_ref and classpath_ref.startswith('${') and classpath_ref.endswith('}'):
                path_id = classpath_ref[2:-1]
                for path_tag in root.findall('path'):
                    if path_tag.get('id') == path_id:
                        ensure_pathelems(path_tag)
                        ensure_srcpath(path_tag)
                        break
    
    # Add Jackson to junit tasks
    for junit in root.findall('.//junit'):
        classpath = junit.find('classpath')
        if classpath is not None:
            if 'refid' in classpath.attrib:
                ref_id = classpath.attrib['refid']
                for path_tag in root.findall('path'):
                    if path_tag.get('id') == ref_id:
                        ensure_pathelems(path_tag)
                        ensure_srcpath(path_tag)
                        break
            else:
                ensure_pathelems(classpath)
                ensure_srcpath(classpath)
        else:
            classpath_ref = junit.get('classpath')
            if classpath_ref and classpath_ref.startswith('${') and classpath_ref.endswith('}'):
                path_id = classpath_ref[2:-1]
                for path_tag in root.findall('path'):
                    if path_tag.get('id') == path_id:
                        ensure_pathelems(path_tag)
                        ensure_srcpath(path_tag)
                        break
    
    # Write the modified file
    tree.write(build_file, encoding='utf-8', xml_declaration=True)


