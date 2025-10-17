#!/usr/bin/env python3
"""
Defects4J Shared Build Setup Script

This script automatically sets up the Defects4J shared build file with Jackson dependencies.
It handles backup, patching, verification, and rollback functionality.

Usage:
    python3 setup_defects4j.py [--rollback] [--verify] [--force]

Options:
    --rollback    Restore the original defects4j.build.xml file
    --verify      Only verify the current setup without making changes
    --force       Force re-application even if already patched
"""

import os
import sys
import shutil
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime


# Configuration
DEFECTS4J_BUILD_FILE = "/defects4j/framework/projects/defects4j.build.xml"
BACKUP_SUFFIX = ".backup"
JACKSON_VERSION = "2.13.0"


def log(message, level="INFO"):
    """Print formatted log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def check_defects4j_installation():
    """Check if Defects4J is properly installed."""
    if not os.path.exists(DEFECTS4J_BUILD_FILE):
        log(f"Defects4J build file not found at {DEFECTS4J_BUILD_FILE}", "ERROR")
        log("Please ensure Defects4J is properly installed", "ERROR")
        return False
    
    # Check if we can write to the file
    if not os.access(DEFECTS4J_BUILD_FILE, os.W_OK):
        log(f"No write permission for {DEFECTS4J_BUILD_FILE}", "ERROR")
        log("Please run with appropriate permissions (e.g., sudo)", "ERROR")
        return False
    
    return True


def create_backup():
    """Create backup of the original defects4j.build.xml file."""
    backup_file = DEFECTS4J_BUILD_FILE + BACKUP_SUFFIX
    
    if os.path.exists(backup_file):
        log(f"Backup already exists: {backup_file}")
        return backup_file
    
    try:
        shutil.copy2(DEFECTS4J_BUILD_FILE, backup_file)
        log(f"Created backup: {backup_file}")
        return backup_file
    except Exception as e:
        log(f"Failed to create backup: {e}", "ERROR")
        return None


def restore_backup():
    """Restore the original defects4j.build.xml from backup."""
    backup_file = DEFECTS4J_BUILD_FILE + BACKUP_SUFFIX
    
    if not os.path.exists(backup_file):
        log(f"No backup file found: {backup_file}", "ERROR")
        return False
    
    try:
        shutil.copy2(backup_file, DEFECTS4J_BUILD_FILE)
        log(f"Restored from backup: {backup_file}")
        return True
    except Exception as e:
        log(f"Failed to restore backup: {e}", "ERROR")
        return False


def is_already_patched():
    """Check if the build file is already patched with Jackson dependencies."""
    try:
        tree = ET.parse(DEFECTS4J_BUILD_FILE)
        root = tree.getroot()
        
        # Check for Jackson properties
        jackson_props = ['jackson.version', 'jackson.core.jar', 'jackson.databind.jar', 'jackson.annotations.jar']
        existing_props = set()
        for prop in root.findall('property'):
            prop_name = prop.attrib.get('name', '')
            if prop_name in jackson_props:
                existing_props.add(prop_name)
        
        # Check for Jackson classpath
        jackson_path_exists = False
        for path_tag in root.findall('path'):
            if path_tag.get('id') == 'd4j.lib.jackson':
                jackson_path_exists = True
                break
        
        # Check if Jackson is referenced in classpaths
        jackson_referenced = False
        for path_tag in root.findall('path'):
            for ref in path_tag.findall('path'):
                if ref.get('refid') == 'd4j.lib.jackson':
                    jackson_referenced = True
                    break
            if jackson_referenced:
                break
        
        # Also check in target classpaths
        if not jackson_referenced:
            for target in root.findall('target'):
                for classpath in target.findall('.//classpath'):
                    for ref in classpath.findall('path'):
                        if ref.get('refid') == 'd4j.lib.jackson':
                            jackson_referenced = True
                            break
                    if jackson_referenced:
                        break
                if jackson_referenced:
                    break
        
        return len(existing_props) == len(jackson_props) and jackson_path_exists and jackson_referenced
        
    except Exception as e:
        log(f"Error checking patch status: {e}", "ERROR")
        return False


def apply_jackson_patch():
    """Apply Jackson dependencies to the Defects4J shared build file."""
    try:
        tree = ET.parse(DEFECTS4J_BUILD_FILE)
        root = tree.getroot()
        
        # Add Jackson properties after cobertura properties
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
        ensure_property('jackson.version', JACKSON_VERSION)
        ensure_property('jackson.core.jar', f"${{d4j.workdir}}/lib/jackson-core-{JACKSON_VERSION}.jar")
        ensure_property('jackson.databind.jar', f"${{d4j.workdir}}/lib/jackson-databind-{JACKSON_VERSION}.jar")
        ensure_property('jackson.annotations.jar', f"${{d4j.workdir}}/lib/jackson-annotations-{JACKSON_VERSION}.jar")
        
        # Add Jackson classpath after test generation libraries
        jackson_path_exists = False
        for path_tag in root.findall('path'):
            if path_tag.get('id') == 'd4j.lib.jackson':
                jackson_path_exists = True
                break
        
        if not jackson_path_exists:
            # Find the test generation path to insert after it
            testgen_path = None
            for path_tag in root.findall('path'):
                if path_tag.get('id') == 'd4j.lib.testgen.rt':
                    testgen_path = path_tag
                    break
            
            jackson_path = ET.Element('path', {'id': 'd4j.lib.jackson'})
            ET.SubElement(jackson_path, 'pathelement', {'location': '${jackson.core.jar}'})
            ET.SubElement(jackson_path, 'pathelement', {'location': '${jackson.databind.jar}'})
            ET.SubElement(jackson_path, 'pathelement', {'location': '${jackson.annotations.jar}'})
            
            if testgen_path is not None:
                # Insert after testgen path
                parent = testgen_path.getparent()
                if parent is not None:
                    index = list(parent).index(testgen_path)
                    parent.insert(index + 1, jackson_path)
                else:
                    root.append(jackson_path)
            else:
                root.append(jackson_path)
        
        # Add Jackson to existing classpaths
        targets_to_update = [
            'run.dev.tests',
            'monitor.test', 
            'mutation.test',
            'compile.gen.tests',
            'run.gen.tests'
        ]
        
        for target in root.findall('target'):
            if target.get('name') in targets_to_update:
                for junit in target.findall('.//junit'):
                    classpath = junit.find('classpath')
                    if classpath is not None:
                        # Check if Jackson path is already referenced
                        jackson_ref_exists = False
                        for ref in classpath.findall('path'):
                            if ref.get('refid') == 'd4j.lib.jackson':
                                jackson_ref_exists = True
                                break
                        
                        if not jackson_ref_exists:
                            ET.SubElement(classpath, 'path', {'refid': 'd4j.lib.jackson'})
                
                for javac in target.findall('.//javac'):
                    classpath = javac.find('classpath')
                    if classpath is not None:
                        # Check if Jackson path is already referenced
                        jackson_ref_exists = False
                        for ref in classpath.findall('path'):
                            if ref.get('refid') == 'd4j.lib.jackson':
                                jackson_ref_exists = True
                                break
                        
                        if not jackson_ref_exists:
                            ET.SubElement(classpath, 'path', {'refid': 'd4j.lib.jackson'})
        
        # Write the modified file
        tree.write(DEFECTS4J_BUILD_FILE, encoding='utf-8', xml_declaration=True)
        log("Successfully applied Jackson dependencies patch")
        return True
        
    except Exception as e:
        log(f"Failed to apply patch: {e}", "ERROR")
        return False


def verify_setup():
    """Verify that the Jackson setup is working correctly."""
    log("Verifying Defects4J Jackson setup...")
    
    # Check if file is patched
    if not is_already_patched():
        log("Defects4J build file is not properly patched", "ERROR")
        return False
    
    # Check if Jackson JARs would be available (simulate a test)
    try:
        # This is a basic verification - in practice, the JARs are downloaded
        # by the Python code when needed
        log("✓ Jackson properties are correctly defined")
        log("✓ Jackson classpath is properly configured")
        log("✓ Jackson is integrated into test and compilation targets")
        log("✓ Setup verification completed successfully")
        return True
    except Exception as e:
        log(f"Verification failed: {e}", "ERROR")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Setup Defects4J shared build file with Jackson dependencies")
    parser.add_argument('--rollback', action='store_true', help='Restore original build file from backup')
    parser.add_argument('--verify', action='store_true', help='Only verify current setup')
    parser.add_argument('--force', action='store_true', help='Force re-application even if already patched')
    
    args = parser.parse_args()
    
    log("Defects4J Jackson Setup Script")
    log("=" * 40)
    
    # Check Defects4J installation
    if not check_defects4j_installation():
        sys.exit(1)
    
    # Handle rollback
    if args.rollback:
        log("Rolling back to original Defects4J build file...")
        if restore_backup():
            log("Rollback completed successfully")
            sys.exit(0)
        else:
            log("Rollback failed", "ERROR")
            sys.exit(1)
    
    # Handle verify-only
    if args.verify:
        if verify_setup():
            log("Setup verification passed")
            sys.exit(0)
        else:
            log("Setup verification failed", "ERROR")
            sys.exit(1)
    
    # Check if already patched
    if is_already_patched() and not args.force:
        log("Defects4J build file is already patched with Jackson dependencies")
        log("Use --force to re-apply the patch")
        sys.exit(0)
    
    # Create backup
    backup_file = create_backup()
    if not backup_file:
        log("Failed to create backup, aborting", "ERROR")
        sys.exit(1)
    
    # Apply patch
    log("Applying Jackson dependencies patch...")
    if apply_jackson_patch():
        log("Patch applied successfully")
        
        # Verify the setup
        if verify_setup():
            log("Setup completed successfully!")
            log(f"Backup saved as: {backup_file}")
            log("You can now use the objdump CLI with Defects4J projects")
        else:
            log("Setup completed but verification failed", "WARNING")
            log("You may need to check the configuration manually")
    else:
        log("Failed to apply patch", "ERROR")
        log("Restoring from backup...")
        restore_backup()
        sys.exit(1)


if __name__ == "__main__":
    main()
