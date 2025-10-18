import json
import logging
import os
import subprocess
from typing import List, Optional


def extract_test_methods(test_class_file: str) -> List[str]:
    """
    Extract test method names from a Java test class file.
    
    Args:
        test_class_file: Path to the Java test class file
        
    Returns:
        List of test method names, empty list if extraction fails
    """
    log = logging.getLogger("test_extractor")
    
    if not os.path.isfile(test_class_file):
        log.warning(f"Test class file not found: {test_class_file}")
        return []
    
    # Find the instrumenter JAR file
    jar_path = find_instrumenter_jar()
    if not jar_path:
        log.warning("Could not find instrumenter JAR file")
        return []
    
    try:
        # Call Java instrumenter with extract-tests command
        result = subprocess.run([
            "java", "-jar", jar_path, "extract-tests", test_class_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            log.warning(f"Failed to extract test methods from {test_class_file}: {result.stderr}")
            return []
        
        # Parse JSON output
        test_methods = json.loads(result.stdout)
        if not isinstance(test_methods, list):
            log.warning(f"Unexpected output format from test extractor: {result.stdout}")
            return []
        
        log.debug(f"Extracted {len(test_methods)} test methods from {test_class_file}")
        return test_methods
        
    except subprocess.TimeoutExpired:
        log.warning(f"Timeout extracting test methods from {test_class_file}")
        return []
    except json.JSONDecodeError as e:
        log.warning(f"Failed to parse JSON output from test extractor: {e}")
        return []
    except Exception as e:
        log.warning(f"Error extracting test methods from {test_class_file}: {e}")
        return []


def find_instrumenter_jar() -> Optional[str]:
    """
    Find the instrumenter JAR file in the project.
    
    Returns:
        Path to the instrumenter JAR file, or None if not found
    """
    # Look for the JAR in the java_instrumenter/target directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    jar_dir = os.path.join(project_root, "java_instrumenter", "target")
    
    # Try different JAR file names
    jar_names = [
        "instrumenter.jar",
        "java-instrumenter-1.0.0.jar"
    ]
    
    for jar_name in jar_names:
        jar_path = os.path.join(jar_dir, jar_name)
        if os.path.isfile(jar_path):
            return jar_path
    
    return None
