from typing import Dict, List, Optional, Set
import os
import re
import logging
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")

from .logging_setup import configure_logging
from .jt_types import BuildSystem
from . import defects4j
from .build_systems import detect
from .build_systems.maven import add_dependencies as add_maven
from .build_systems.ant import add_dependencies as add_ant
from .instrumentation.diff import compute_file_diff_ranges_both
from .instrumentation.ts import extract_changed_methods
from .instrumentation.instrumenter import instrument_changed_methods
from .instrumentation.helpers import ensure_helper_sources
from .objdump_io.net import download_files


def download_jackson_jars(work_dir: str, version: str = "2.13.0") -> None:
    lib_dir = os.path.join(work_dir, "lib")
    items = [
        (f"jackson-core-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/{version}/jackson-core-{version}.jar"),
        (f"jackson-databind-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/{version}/jackson-databind-{version}.jar"),
        (f"jackson-annotations-{version}.jar", f"https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-annotations/{version}/jackson-annotations-{version}.jar"),
    ]
    download_files(lib_dir, items)


def run_all(project_id: str, bug_id: str, work_dir: str, jackson_version: str = "2.13.0", instrument_all_modified: bool = False, report_file: Optional[str] = None) -> None:
    configure_logging()
    log = logging.getLogger("jackson_installer")

    if os.path.exists(work_dir):
        log.info("Removing existing work dir: %s", work_dir)
        import shutil
        shutil.rmtree(work_dir)

    log.info("Checkout buggy version to %s", work_dir)
    if not defects4j.checkout(project_id, bug_id, work_dir, "b"):
        raise RuntimeError("checkout buggy failed")

    fixed_dir = f"{work_dir}_fixed"
    if os.path.exists(fixed_dir):
        import shutil
        shutil.rmtree(fixed_dir)
    log.info("Checkout fixed version to %s", fixed_dir)
    if not defects4j.checkout(project_id, bug_id, fixed_dir, "f"):
        raise RuntimeError("checkout fixed failed")

    build_system = detect(work_dir)
    if build_system == BuildSystem.MAVEN:
        log.info("Detected Maven build system")
        pom_path = os.path.join(work_dir, "pom.xml")
        add_maven(pom_path, jackson_version)
    elif build_system == BuildSystem.ANT:
        log.info("Detected Ant build system")
    else:
        raise RuntimeError("Unknown build system")
    # Defects4J uses Ant under the hood; ensure Ant build has Jackson jars regardless
    build_xml = os.path.join(work_dir, "build.xml")
    if os.path.isfile(build_xml):
        add_ant(build_xml, jackson_version)

    # Ensure a default dump file exists for compile phase; actual dumps occur during test runs
    out_file = os.path.join(work_dir, "dump.jsonl")
    env_vars = {"OBJDUMP_OUT": out_file}
    defects4j.compile(work_dir, env=env_vars)

    classes_dir = defects4j.export(work_dir, "dir.src.classes") or ""
    modified_classes = (defects4j.export(work_dir, "classes.modified") or "").splitlines()
    modified_classes = [s for s in (c.strip() for c in modified_classes) if s]

    def to_path(class_path: str, modified: List[str]) -> List[str]:
        result: List[str] = []
        for mc in modified:
            cp = mc.replace(".", "/")
            result.append(os.path.join(class_path, cp))
        return result

    modified_class_paths = to_path(classes_dir, modified_classes) if classes_dir and modified_classes else []

    changed: Dict[str, List[str]] = {}
    # compute changes
    for buggy_cp in modified_class_paths:
        java_buggy = os.path.join(work_dir, buggy_cp + ".java")
        java_fixed = os.path.join(fixed_dir, buggy_cp + ".java")
        if not (os.path.isfile(java_buggy) and os.path.isfile(java_fixed)):
            continue
        ranges = compute_file_diff_ranges_both(java_buggy, java_fixed)
        methods = set()
        if ranges.get("left"):
            methods.update(extract_changed_methods(java_buggy, ranges["left"]))
        if ranges.get("right"):
            methods.update(extract_changed_methods(java_fixed, ranges["right"]))
        if methods:
            changed[java_buggy] = sorted(methods)

    src_java_rel = defects4j.export(work_dir, "dir.src.java") or "src/main/java"
    ensure_helper_sources(work_dir, src_java_rel)
    download_jackson_jars(work_dir, jackson_version)

    instrumented_map: Dict[str, List[str]] = {}
    if changed:
        instrumented_map = instrument_changed_methods(changed)
    else:
        if instrument_all_modified and modified_class_paths:
            # Collect all methods in modified files
            from tree_sitter import Parser
            from tree_sitter_languages import get_language
            all_map: Dict[str, List[str]] = {}
            for p in modified_class_paths:
                jf = os.path.join(work_dir, p + ".java")
                if not os.path.isfile(jf):
                    continue
                try:
                    lang = get_language("java")
                    parser = Parser()
                    parser.set_language(lang)
                    with open(jf, "rb") as f:
                        s = f.read()
                    t = parser.parse(s)
                    cursor = t.walk()
                    stack = [cursor.node]
                    sigs: Set[str] = set()
                    from .instrumentation.ts import method_signature_from_node
                    while stack:
                        n = stack.pop()
                        if n.type in ("method_declaration", "constructor_declaration"):
                            sigs.add(method_signature_from_node(s, n))
                        for i in range(n.child_count):
                            stack.append(n.child(i))
                    if sigs:
                        all_map[jf] = sorted(sigs)
                except Exception:
                    continue
            if all_map:
                instrumented_map = instrument_changed_methods(all_map)

    # Emit instrumented method paths report (pretty stdout and JSON file)
    try:
        flat: List[str] = []
        for fpath, sigs in instrumented_map.items():
            abs_path = os.path.abspath(fpath)
            for sig in sigs:
                flat.append(f"{abs_path}::{sig}")
        if report_file is None:
            report_file = os.path.join(work_dir, "instrumented_methods.json")
        payload = json.dumps(sorted(flat))
        # Pretty stdout for humans; keep JSON in file for tools
        try:
            grouped: Dict[str, List[str]] = {}
            for item in sorted(flat):
                path, sig = item.split("::", 1)
                grouped.setdefault(path, []).append(sig)
            total = sum(len(v) for v in grouped.values())
            print(f"Fixed methods ({total}):")
            for path in sorted(grouped.keys()):
                print(f"- {path}")
                for sig in grouped[path]:
                    print(f"  - {sig}")
        except Exception:
            # Fallback to raw JSON on stdout if pretty printing fails
            print(payload)
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as rf:
            rf.write(payload)
    except Exception:
        # Do not fail the workflow on reporting errors
        pass

    # Prepare dumps directory for per-test outputs
    dumps_dir = os.path.join(work_dir, "dumps")
    try:
        os.makedirs(dumps_dir, exist_ok=True)
    except Exception:
        pass

    defects4j.compile(work_dir, env=env_vars)
    tests = defects4j.export(work_dir, "tests.trigger")
    if tests:
        names = [t.strip() for t in tests.splitlines() if t.strip()]
        # Print triggering test list for visibility
        try:
            print(f"Triggering tests ({len(names)}):")
            for name in names:
                print(f"- {name}")
        except Exception:
            pass
        for name in names:
            safe = re.sub(r"[^A-Za-z0-9]", "-", name)
            dump_path = os.path.join(dumps_dir, f"{safe}.jsonl")
            abs_dump_path = os.path.abspath(dump_path)
            print(f"Running test {name} with dump path {abs_dump_path}")
            per_test_env = {"OBJDUMP_OUT": abs_dump_path}
            defects4j.test(work_dir, [name], env=per_test_env)
    else:
        # Fall back to running the full test suite if no triggering tests are exported
        try:
            print("No triggering tests exported; running full test suite.")
        except Exception:
            pass
        defects4j.test(work_dir, env=env_vars)


