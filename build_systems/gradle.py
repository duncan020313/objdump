import logging
from pathlib import Path
from typing import Optional


log = logging.getLogger(__name__)


def setup_jackson_dependencies(work_dir: str, jackson_version: str = "2.13.0") -> None:
    """
    Ensure Gradle project uses Jackson via Gradle dependencies (not local libs).

    This function adds the Jackson modules to the project's Gradle build file
    and ensures a Maven repository (mavenCentral) is available so Defects4J
    builds will resolve them.

    - Prefer the configuration used in the existing script (implementation/api/compile).
    - Avoid duplicating dependencies if already present.
    - Support both Groovy DSL (build.gradle) and Kotlin DSL (build.gradle.kts).

    Args:
        work_dir: Project directory containing Gradle build files
        jackson_version: Jackson version string (e.g., "2.13.0")
    """
    project_dir = Path(work_dir)
    if not project_dir.is_dir():
        raise ValueError(f"work_dir does not exist: {work_dir}")

    # Prefer Groovy DSL, then Kotlin DSL
    gradle_groovy = project_dir / "build.gradle"
    gradle_kts = project_dir / "build.gradle.kts"

    if gradle_groovy.is_file():
        log.info("Configuring Jackson in build.gradle")
        _ensure_gradle_dependencies_groovy(str(gradle_groovy), jackson_version)
    elif gradle_kts.is_file():
        log.info("Configuring Jackson in build.gradle.kts")
        _ensure_gradle_dependencies_kts(str(gradle_kts), jackson_version)
    else:
        log.warning("No Gradle build file found (build.gradle/build.gradle.kts); skipping")


def _ensure_gradle_dependencies_groovy(build_file_path: str, jackson_version: str) -> None:
    p = Path(build_file_path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    # Determine dependency configuration keyword
    configuration = _detect_configuration_keyword(text)

    # Jackson coordinates
    deps = [
        f"com.fasterxml.jackson.core:jackson-core:{jackson_version}",
        f"com.fasterxml.jackson.core:jackson-databind:{jackson_version}",
        f"com.fasterxml.jackson.core:jackson-annotations:{jackson_version}",
    ]

    # Avoid duplicates
    missing = [d for d in deps if d not in text]
    if not missing:
        p.write_text(text, encoding="utf-8")
        return

    # Inject into dependencies { ... }
    injected_lines = "\n".join([f"    {configuration} '{d}'" for d in missing])

    if "dependencies" in text:
        # Insert just before the first closing brace of the first dependencies block
        new_text = _inject_into_first_block(text, "dependencies", injected_lines)
        if new_text is None:
            # Fallback: append a dependencies block
            new_text = text.rstrip() + "\n\ndependencies {\n" + injected_lines + "\n}\n"
    else:
        # Append a dependencies block at the end
        new_text = text.rstrip() + "\n\ndependencies {\n" + injected_lines + "\n}\n"

    p.write_text(new_text, encoding="utf-8")


def _ensure_gradle_dependencies_kts(build_file_path: str, jackson_version: str) -> None:
    p = Path(build_file_path)
    text = p.read_text(encoding="utf-8", errors="ignore")

    # Ensure repositories include mavenCentral()
    text = _ensure_repositories_kts(text)

    # Determine dependency configuration keyword
    configuration = _detect_configuration_keyword(text, kts=True)

    # Jackson coordinates
    deps = [
        f"com.fasterxml.jackson.core:jackson-core:{jackson_version}",
        f"com.fasterxml.jackson.core:jackson-databind:{jackson_version}",
        f"com.fasterxml.jackson.core:jackson-annotations:{jackson_version}",
    ]

    # Avoid duplicates
    missing = [d for d in deps if d not in text]
    if not missing:
        p.write_text(text, encoding="utf-8")
        return

    injected_lines = "\n".join([f"    {configuration}(\"{d}\")" for d in missing])

    if "dependencies {" in text:
        new_text = _inject_into_first_block(text, "dependencies", injected_lines)
        if new_text is None:
            new_text = text.rstrip() + "\n\ndependencies {\n" + injected_lines + "\n}\n"
    else:
        new_text = text.rstrip() + "\n\ndependencies {\n" + injected_lines + "\n}\n"

    p.write_text(new_text, encoding="utf-8")

def _ensure_repositories_kts(text: str) -> str:
    if "repositories {" not in text:
        return "repositories {\n    mavenCentral()\n}\n\n" + text
    if "mavenCentral()" in text:
        return text
    injected = "    mavenCentral()"
    new_text = _inject_into_first_block(text, "repositories", injected)
    if new_text is not None:
        return new_text
    return text.rstrip() + "\n\nrepositories {\n    mavenCentral()\n}\n"

def _detect_configuration_keyword(text: str, kts: bool = False) -> str:
    # Respect existing conventions; default to 'compile' for legacy projects
    if " api " in f" {text} ":
        return "api"
    if " implementation " in f" {text} ":
        return "implementation"
    # Look for legacy
    if " compile " in f" {text} ":
        return "compile"
    # Kotlin DSL often uses implementation/api; default sensibly
    return "implementation" if kts else "compile"


def _inject_into_first_block(text: str, block_name: str, injected_lines: str) -> Optional[str]:
    """
    Inject lines before the first closing brace of the first matching TOP-LEVEL block.
    We walk the file maintaining a brace depth and only match `block_name {` when
    depth == 0, ensuring we don't inject into nested scopes like subprojects {}.
    """
    start_token = f"{block_name} {{"

    # Scan for the first top-level occurrence of the block
    depth = 0
    i = 0
    while i < len(text):
        c = text[i]
        if c == '{':
            depth += 1
            i += 1
            continue
        if c == '}':
            depth -= 1
            if depth < 0:
                depth = 0
            i += 1
            continue

        # Only consider matches at top level
        if depth == 0 and text.startswith(start_token, i):
            # We found the start of the desired top-level block. Find its matching closing brace.
            # Locate the opening brace index just after the token
            open_brace_idx = text.find('{', i)
            if open_brace_idx == -1:
                return None

            inner_depth = 0
            j = open_brace_idx
            while j < len(text):
                cj = text[j]
                if cj == '{':
                    inner_depth += 1
                elif cj == '}':
                    inner_depth -= 1
                    if inner_depth == 0:
                        # Insert just before j
                        before = text[:j].rstrip()
                        after = text[j:]
                        insertion = ("\n" + injected_lines + "\n")
                        return before + insertion + after
                j += 1
            return None

        i += 1

    return None