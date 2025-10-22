import logging
from pathlib import Path
from typing import Optional
import re


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

    # Also update any .bnd files in the project to include org.instrument.*
    update_bnd_files(work_dir)


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


def update_bnd_files(work_dir: str) -> None:
    """
    Recursively find *.bnd files and ensure both Import-Package and Private-Package
    include 'org.instrument.*' exactly once, preserving formatting where possible.
    """
    project_dir = Path(work_dir)
    if not project_dir.exists():
        return

    for bnd_path in project_dir.rglob("*.bnd"):
        try:
            text = bnd_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        original_text = text
        package_contents = ["org.instrument.*,\\",
        "com.fasterxml.jackson.annotation,\\",
        "com.fasterxml.jackson.core,\\",
        "com.fasterxml.jackson.databind,\\",
        "com.fasterxml.jackson.databind.introspect,\\",
        "com.fasterxml.jackson.databind.module,\\"]
        for content in package_contents:
            text = _ensure_bnd_key(text, key="Import-Package", value=content)
        text = _ensure_bnd_key(text, key="Private-Package", value="org.instrument.*")

        if text != original_text:
            try:
                bnd_path.write_text(text, encoding="utf-8")
                log.info("Updated BND file: %s", bnd_path)
            except Exception:
                # Skip files we cannot write
                pass


def _ensure_bnd_key(text: str, key: str, value: str) -> str:
    """
    Ensure a BND property `key` contains `value`.

    - Preserves existing formatting (delimiter, indentation, continuations) when possible
    - Avoids inserting duplicates
    - Creates the property if missing using `default_delim`
    """
    header_re = re.compile(rf"(?m)^(?P<key>{re.escape(key)})\s*(?P<delim>[:=])\s*(?P<rest>.*)$")
    m = header_re.search(text)
    if not m:
        log.error("Could not find property %s in %s", key, text)
        return text

    start = m.start()
    end = m.end()

    # Determine the block (header + any continuation lines) boundaries
    # The block ends before the next blank line or next header-like line
    lines = text[end:].splitlines(keepends=True)
    block_extra_len = 0
    for _, line in enumerate(lines):
        # Stop if we hit a blank line
        if line.strip() == "":
            break
        # Stop if we hit a new property header (e.g., Something: or Something=)
        if re.match(r"^[A-Za-z0-9_.-]+\s*[:=]", line):
            break
        block_extra_len += len(line)

    block_start = start
    block_end = end + block_extra_len
    block_text = text[block_start:block_end]

    # If value already within this block, return original text
    if value in block_text:
        return text

    # Split the block into header and continuation lines
    header_line_end = block_text.find("\n")
    if header_line_end == -1:
        header_line = block_text
        cont = ""
    else:
        header_line = block_text[:header_line_end]
        cont = block_text[header_line_end + 1 :]

    # Decide how to insert depending on whether we have continuation lines
    if not cont:
        # Single-line property: append inline with a comma
        # Keep spacing after delimiter as-is
        if header_line.rstrip().endswith("\\"):
            # Already using continuation, add a new line with a reasonable indent
            indent = " " * 16
            new_block = header_line + "\n" + indent + value
        else:
            # Append inline
            new_block = header_line.rstrip() + ", " + value
    else:
        # Multi-line continuation block
        cont_lines = cont.splitlines()
        # Determine indentation from first continuation line
        m_indent = re.match(r"^\s*", cont_lines[0]) if cont_lines else None
        indent = m_indent.group(0) if m_indent else " " * 4

        # Ensure the last non-empty continuation line ends with a comma and continuation if pattern uses \
        last_idx = len(cont_lines) - 1
        while last_idx >= 0 and cont_lines[last_idx].strip() == "":
            last_idx -= 1
        if last_idx >= 0:
            last_line = cont_lines[last_idx].rstrip("\r\n")
            # If it ends with a backslash, ensure comma before it; else append comma
            if last_line.rstrip().endswith("\\"):
                # Insert comma before trailing backslash if missing
                core = last_line.rstrip()
                if not re.search(r",\s*\\$", core):
                    core = re.sub(r"\\+$", lambda _m: ", \\", core)
                cont_lines[last_idx] = core
            else:
                cont_lines[last_idx] = last_line + ", \\\\"  # add continuation

        # Append the new value line
        cont_lines.append(f"{indent}{value}")
        cont = "\n".join(cont_lines)
        new_block = header_line + "\n" + cont

    # Rebuild the text
    return text[:block_start] + new_block + text[block_end:]