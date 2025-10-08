from typing import Dict, List, Set
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")
from tree_sitter import Parser
from tree_sitter_languages import get_language
from .ts import method_signature_from_node


def instrument_java_file(java_file: str, target_signatures: List[str]) -> List[str]:
    if not target_signatures:
        return []
    language = get_language("java")
    parser = Parser()
    parser.set_language(language)
    try:
        with open(java_file, "rb") as f:
            src = f.read()
    except FileNotFoundError:
        return []

    tree = parser.parse(src)
    cursor = tree.walk()
    stack = [cursor.node]
    method_nodes = []
    matched_sigs: List[str] = []
    while stack:
        n = stack.pop()
        if n.type in ("method_declaration", "constructor_declaration"):
            sig = method_signature_from_node(src, n)
            if sig in target_signatures:
                method_nodes.append(n)
                matched_sigs.append(sig)
        for i in range(n.child_count):
            stack.append(n.child(i))
    if not method_nodes:
        return []

    text = src.decode("utf-8")
    import_needed = ["import org.instrument.DumpObj;", "import org.instrument.DebugDump;"]
    missing_imports = [imp for imp in import_needed if imp not in text]
    if missing_imports:
        pkg_idx = text.find("package ")
        insert_pos = 0
        if pkg_idx >= 0:
            semi = text.find(";", pkg_idx)
            if semi >= 0:
                insert_pos = semi + 1
        header = text[:insert_pos]
        rest = text[insert_pos:]
        add = "\n" + "\n".join(missing_imports) + "\n"
        text = header + add + rest

    src = text.encode("utf-8")
    tree = parser.parse(src)
    cursor = tree.walk()
    stack = [cursor.node]
    method_nodes = []
    while stack:
        n = stack.pop()
        if n.type in ("method_declaration", "constructor_declaration"):
            sig = method_signature_from_node(src, n)
            if sig in target_signatures:
                method_nodes.append(n)
        for i in range(n.child_count):
            stack.append(n.child(i))

    method_nodes.sort(key=lambda n: n.start_byte, reverse=True)
    new_src = bytearray(src)
    for n in method_nodes:
        body = n.child_by_field_name("body")
        if body is None or body.type != "block":
            continue
        is_static = False
        for i in range(n.child_count):
            child = n.child(i)
            if child.type == "modifiers":
                text_slice = src[child.start_byte:child.end_byte].decode("utf-8")
                if "static" in text_slice.split():
                    is_static = True
                    break
        body_start = body.start_byte
        body_end = body.end_byte
        inner = new_src[body_start:body_end]
        if not inner or inner[0] != ord('{') or inner[-1] != ord('}'):
            continue
        target_expr = b"null" if is_static else b"this"
        params_node = n.child_by_field_name("parameters")
        params_text = src[params_node.start_byte:params_node.end_byte].decode("utf-8") if params_node else "()"
        param_names: List[str] = []
        if params_text and len(params_text) >= 2:
            inside = params_text[1:-1].strip()
            if inside:
                for part in inside.split(','):
                    name = part.strip().split()[-1]
                    name = name.replace("...", "").replace("@", "").strip()
                    name = name.replace(")", "").replace("(", "")
                    if name:
                        param_names.append(name)
        map_init = b"\njava.util.Map params = new java.util.LinkedHashMap();\n"
        for pn in param_names:
            map_init += (b"params.put(\"" + pn.encode("utf-8") + b"\", " + pn.encode("utf-8") + b");\n")
        id_var = b"String dumpId = DebugDump.newInvocationId();\nboolean __dumped = false;\n"
        entry = id_var + map_init + b"DebugDump.writeEntry(" + target_expr + b", params, dumpId);\ntry "
        exitf = b" finally { if (!__dumped) { java.util.Map params = new java.util.LinkedHashMap(); DebugDump.writeExit(" + target_expr + b", params, null, dumpId); } }\n"

        is_constructor = (n.type == "constructor_declaration")
        content = inner[1:-1]
        header_stmt = b""
        rest_content = content
        if is_constructor:
            semi_idx = content.find(b";")
            if semi_idx != -1:
                first_stmt = content[:semi_idx + 1]
                if b"super(" in first_stmt or b"this(" in first_stmt:
                    header_stmt = first_stmt + b"\n"
                    rest_content = content[semi_idx + 1:]
        if header_stmt:
            new_body = b"{" + header_stmt + entry + b"{" + rest_content + b"}" + exitf + b"}"
        else:
            new_body = b"{" + entry + b"{" + content + b"}" + exitf + b"}"
        new_src[body_start:body_end] = new_body

    with open(java_file, "wb") as f:
        f.write(bytes(new_src))

    src2 = bytes(new_src)
    tree2 = parser.parse(src2)
    cursor2 = tree2.walk()
    stack2 = [cursor2.node]
    targets2 = []
    while stack2:
        n = stack2.pop()
        if n.type in ("method_declaration", "constructor_declaration"):
            sig = method_signature_from_node(src2, n)
            if sig in target_signatures:
                targets2.append(n)
        for i in range(n.child_count):
            stack2.append(n.child(i))
    targets2.sort(key=lambda n: n.start_byte, reverse=True)
    new_src2 = bytearray(src2)
    for n in targets2:
        insert_at = n.start_byte
        if b"@DumpObj" in new_src2[max(0, insert_at - 100):insert_at]:
            continue
        new_src2[insert_at:insert_at] = b"\n@DumpObj\n"

    with open(java_file, "wb") as f:
        f.write(bytes(new_src2))

    src3 = bytes(new_src2)
    tree3 = parser.parse(src3)
    cursor3 = tree3.walk()
    stack3 = [cursor3.node]
    target_methods3 = []
    while stack3:
        n = stack3.pop()
        if n.type in ("method_declaration", "constructor_declaration"):
            sig = method_signature_from_node(src3, n)
            if sig in target_signatures:
                target_methods3.append(n)
        for i in range(n.child_count):
            stack3.append(n.child(i))
    target_methods3.sort(key=lambda n: n.start_byte, reverse=True)
    new_src3 = bytearray(src3)
    for mnode in target_methods3:
        is_static = False
        for i in range(mnode.child_count):
            child = mnode.child(i)
            if child.type == "modifiers":
                txt = src3[child.start_byte:child.end_byte].decode("utf-8")
                if "static" in txt.split():
                    is_static = True
                    break
        self_expr = b"null" if is_static else b"this"
        body = mnode.child_by_field_name("body")
        if body is None:
            continue
        returns = []
        stackb = [body]
        while stackb:
            bn = stackb.pop()
            if bn.type == "return_statement":
                returns.append(bn)
            for i in range(bn.child_count):
                stackb.append(bn.child(i))
        returns.sort(key=lambda n: n.start_byte, reverse=True)
        for r in returns:
            expr_child = None
            for i in range(r.child_count):
                ch = r.child(i)
                if ch.type not in ("return", ";"):
                    expr_child = ch
                    break
            if expr_child is not None:
                expr_bytes = new_src3[expr_child.start_byte:expr_child.end_byte]
                replacement = (
                    b"{ java.util.Map params = new java.util.LinkedHashMap(); "
                    b"DebugDump.writeExit(" + self_expr + b", params, (Object)(" + expr_bytes + b"), dumpId); __dumped = true; return " + expr_bytes + b"; }"
                )
            else:
                replacement = (
                    b"{ java.util.Map params = new java.util.LinkedHashMap(); "
                    b"DebugDump.writeExit(" + self_expr + b", params, null, dumpId); __dumped = true; return; }"
                )
            new_src3[r.start_byte:r.end_byte] = replacement

    with open(java_file, "wb") as f:
        f.write(bytes(new_src3))
    # Return the list of method signatures that were instrumented in this file
    return sorted(set(matched_sigs))


def instrument_changed_methods(changed_methods: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Instrument methods per file and return mapping of file -> instrumented signatures."""
    result: Dict[str, List[str]] = {}
    for fpath, sigs in changed_methods.items():
        try:
            instrumented = instrument_java_file(fpath, sigs)
            if instrumented:
                result[fpath] = sorted(instrumented)
        except Exception:
            # Keep going on best-effort; caller can log
            continue
    return result


