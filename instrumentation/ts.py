from typing import List, Set, Tuple
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")
from tree_sitter import Parser
from tree_sitter_languages import get_language


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

    return sorted(method_signatures)


def method_signature_from_node(source_bytes: bytes, node) -> str:
    name_node = node.child_by_field_name("name")
    params_node = node.child_by_field_name("parameters")
    type_node = node.child_by_field_name("type")
    name_text = source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8") if name_node else "<anonymous>"
    params_text = source_bytes[params_node.start_byte:params_node.end_byte].decode("utf-8") if params_node else "()"
    return_text = source_bytes[type_node.start_byte:type_node.end_byte].decode("utf-8") + " " if type_node else ""
    return (return_text + name_text + params_text).strip()


