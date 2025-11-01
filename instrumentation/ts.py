from typing import Any, Dict, List, Set, Tuple
import re
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")
from tree_sitter import Parser
from tree_sitter_languages import get_language
import logging
log = logging.getLogger(__name__)


def extract_changed_methods(java_source: str, changed_ranges: List[Tuple[int, int]]) -> List[str]:
    language = get_language("java")
    parser = Parser()
    parser.set_language(language)
    try:
        with open(java_source, "rb") as f:
            source_bytes = f.read()
    except FileNotFoundError:
        return []
    tree = parser.parse(source_bytes)

    changed_lines: Set[int] = set()
    for start, end in changed_ranges:
        for ln in range(start, end + 1):
            changed_lines.add(ln)

    def node_spans_changed_lines(node) -> bool:
        srow, _ = node.start_point
        erow, _ = node.end_point
        start_line = srow + 1
        end_line = erow + 1
        for ln in changed_lines:
            if start_line <= ln <= end_line:
                return True
        return False

    def slice_bytes(start_byte: int, end_byte: int) -> bytes:
        return source_bytes[start_byte:end_byte]

    cursor = tree.walk()
    stack = [cursor.node]
    method_signatures: Set[str] = set()
    while stack:
        node = stack.pop()
        if node.type in ("method_declaration", "constructor_declaration") and node_spans_changed_lines(node):
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            type_node = node.child_by_field_name("type")
            name_text = slice_bytes(name_node.start_byte, name_node.end_byte).decode("utf-8") if name_node else "<anonymous>"
            params_text = slice_bytes(params_node.start_byte, params_node.end_byte).decode("utf-8") if params_node else "()"
            return_text = slice_bytes(type_node.start_byte, type_node.end_byte).decode("utf-8") + " " if type_node else ""
            method_signatures.add((return_text + name_text + params_text).strip())
        for i in range(node.child_count):
            c = node.child(i)
            if c is not None:
                stack.append(c)

    if len(method_signatures) == 0:
        log.warning(f"No method signatures found in {java_source}. changed_ranges: {changed_ranges}")
        return []

    return sorted(method_signatures)


def method_signature_from_node(source_bytes: bytes, node) -> str:
    name_node = node.child_by_field_name("name")
    params_node = node.child_by_field_name("parameters")
    type_node = node.child_by_field_name("type")
    name_text = source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8") if name_node else "<anonymous>"
    params_text = source_bytes[params_node.start_byte:params_node.end_byte].decode("utf-8") if params_node else "()"
    return_text = source_bytes[type_node.start_byte:type_node.end_byte].decode("utf-8") + " " if type_node else ""
    return (return_text + name_text + params_text).strip()


def _normalize_signature(signature: str) -> str:
    normalized = re.sub(r"\bfinal\s+", "", signature)
    normalized = re.sub(r"\n", "", normalized)
    normalized = re.sub(r"Nullable ", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)
    normalized = re.sub(r"[^a-zA-Z0-9\s\(\),<>\{\}\[\]]", "", normalized)
    return normalized.strip()


def _extract_method_name(signature: str) -> str:
    before_paren = signature.split("(")[0].strip()
    if not before_paren:
        return ""
    parts = before_paren.split()
    return parts[-1] if parts else ""


def _node_text(source_bytes: bytes, node) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")


def _collect_invoked_names(source_bytes: bytes, node) -> Set[str]:
    if node is None:
        return set()
    names: Set[str] = set()
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == "method_invocation":
            name_node = current.child_by_field_name("name")
            if name_node is not None:
                names.add(_node_text(source_bytes, name_node))
        elif current.type == "method_reference":
            name_node = current.child_by_field_name("name")
            if name_node is not None:
                names.add(_node_text(source_bytes, name_node))
        elif current.type == "object_creation_expression":
            type_node = current.child_by_field_name("type")
            if type_node is not None:
                type_text = _node_text(source_bytes, type_node)
                simple_name = type_text.split(".")[-1]
                names.add(simple_name)
        for i in range(current.child_count):
            child = current.child(i)
            if child is not None:
                stack.append(child)
    return names


def find_relevant_methods(java_source: str, target_signatures: List[str], limit: int = 3) -> Dict[str, List[str]]:
    if not target_signatures:
        return {}

    language = get_language("java")
    parser = Parser()
    parser.set_language(language)

    try:
        with open(java_source, "rb") as f:
            source_bytes = f.read()
    except FileNotFoundError:
        normalized_targets = {_normalize_signature(sig): [] for sig in target_signatures}
        return normalized_targets

    tree = parser.parse(source_bytes)

    method_infos: List[Dict[str, Any]] = []

    def visit(node) -> None:
        if node.type in ("method_declaration", "constructor_declaration"):
            signature = method_signature_from_node(source_bytes, node)
            normalized_signature = _normalize_signature(signature)
            name_node = node.child_by_field_name("name")
            method_name = _node_text(source_bytes, name_node) if name_node is not None else ""
            body_node = node.child_by_field_name("body")
            body_text = _node_text(source_bytes, body_node) if body_node is not None else ""
            invoked_names = _collect_invoked_names(source_bytes, body_node)
            method_infos.append(
                {
                    "signature": signature,
                    "normalized": normalized_signature,
                    "name": method_name,
                    "body_text": body_text,
                    "invoked": invoked_names,
                }
            )
        for child in node.children:
            visit(child)

    visit(tree.root_node)

    normalized_targets = {_normalize_signature(sig): sig for sig in target_signatures}
    result: Dict[str, List[str]] = {key: [] for key in normalized_targets.keys()}

    pattern_cache: Dict[str, re.Pattern] = {}

    for target_norm, original_sig in normalized_targets.items():
        target_info = next((info for info in method_infos if info["normalized"] == target_norm), None)
        target_name = target_info["name"] if target_info else _extract_method_name(original_sig)
        if not target_name:
            result[target_norm] = []
            continue

        if target_name not in pattern_cache:
            pattern_cache[target_name] = re.compile(r"\b" + re.escape(target_name) + r"\b")
        call_candidates: List[str] = []
        usage_candidates: List[str] = []

        for info in method_infos:
            if info["normalized"] == target_norm:
                continue
            if target_name in info["invoked"]:
                call_candidates.append(info["signature"])
            else:
                if pattern_cache[target_name].search(info["body_text"]):
                    usage_candidates.append(info["signature"])

        selected: List[str] = []
        for candidate in call_candidates:
            if len(selected) >= limit:
                break
            selected.append(candidate)

        if len(selected) < limit:
            for candidate in usage_candidates:
                if len(selected) >= limit:
                    break
                selected.append(candidate)

        result[target_norm] = selected

    return result


