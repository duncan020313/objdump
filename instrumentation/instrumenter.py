from typing import Dict, List, Set, Tuple, Any
import subprocess
import json
import os
from pathlib import Path
import shutil
import logging  

log = logging.getLogger(__name__)       

def get_instrumenter_jar_path() -> str:
    """Get the path to the Java instrumenter JAR"""
    # Assuming this file is in /root/objdump/instrumentation/instrumenter.py
    # The JAR is at /root/objdump/java_instrumenter/target/instrumenter.jar
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jar_path = os.path.join(current_dir, "java_instrumenter", "target", "instrumenter.jar")
    if not os.path.exists(jar_path):
        raise FileNotFoundError(f"Instrumenter JAR not found at {jar_path}. Please build it first.")
    return jar_path


def normalize_signature(signature: str) -> str:
    """Normalize a Java method signature by removing 'final' modifiers from parameters."""
    import re
    # Remove 'final' keyword from parameter types in the signature
    # Pattern matches: final <type> <name> and replaces with <type> <name>
    normalized = re.sub(r'\bfinal\s+', '', signature)
    normalized = re.sub(r'\n', '', normalized)
    normalized = re.sub(r"[^a-zA-Z0-9\s\(\),\<\>\{\}\[\]]", "", normalized)
    return normalized

def instrument_java_file(java_file: str, target_signatures: List[str]) -> List[Dict[str, Any]]:
    """Instrument a Java file using Java-based instrumenter and return method information.
    
    Returns a list of dicts, each containing:
    - signature: method signature
    - javadoc: parsed JavaDoc (or None)
    - code: original method source code
    """
    if not target_signatures:
        log.warning(f"No target signatures for {java_file}")
        return []
    
    if not os.path.exists(java_file):
        log.warning(f"Java file not found: {java_file}")
        return []
    
    # Normalize target signatures to remove 'final' modifiers
    normalized_signatures = [normalize_signature(sig) for sig in target_signatures]
    
    # Get JAR path
    jar_path = get_instrumenter_jar_path()
    
    # Build command: java -jar instrumenter.jar instrument <file> <sig1> <sig2> ...
    cmd = ["java", "-jar", jar_path, "instrument", java_file] + normalized_signatures
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode:
            # Instrumentation failed
            log.error(f"Instrumentation failed for {java_file}. Return code: {result.returncode}")
            if result.stderr:
                log.error(f"Error output: {result.stderr}")
            if result.stdout:
                log.error(f"Standard output: {result.stdout}")
            return []
        
        # Parse JSON output
        output = json.loads(result.stdout)
        
        # Convert to expected format
        results = []
        for item in output:
            # Handle javadoc field - can be null or object
            javadoc = item.get("javadoc")
            if javadoc is not None:
                # Ensure all expected fields are present
                if "params" not in javadoc:
                    javadoc["params"] = {}
                if "returns" not in javadoc:
                    javadoc["returns"] = None
                if "throws" not in javadoc:
                    javadoc["throws"] = {}
            
            results.append({
                "signature": item["signature"],
                "javadoc": javadoc,
                "code": item["code"]
            })
        
        return results
        
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        # On any error, return empty list
        log.error(f"Error instrumenting {java_file}: {e}")
        return []


def instrument_changed_methods(changed_methods: Dict[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
    """Instrument methods per file and return mapping of file -> method info (signature, javadoc, code)."""
    result: Dict[str, List[Dict[str, Any]]] = {}
    for fpath, sigs in changed_methods.items():
        log.info(f"Instrumenting {fpath} with {sigs}")
        instrumented = instrument_java_file(fpath, sigs)
        if instrumented:
            result[fpath] = instrumented
    return result

def copy_java_template_to_classdir(work_dir: str, class_dir: str) -> None:
    """Copy the Java template to the class directory."""
    src_path =  Path(__file__).parent.parent / "java_templates"
    dst_path = Path(work_dir) / Path(class_dir) / "org" / "instrument"
    if not src_path.exists():
        raise FileNotFoundError(f"Java template not found at {src_path}")
    if dst_path.exists():
        shutil.rmtree(dst_path)
    shutil.copytree(src_path, dst_path)