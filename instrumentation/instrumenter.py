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
    
    # Find all target methods
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
    
    # Add necessary imports (Java 6 compatible)
    import_needed = [
        "import org.instrument.DumpObj;", 
        "import org.instrument.DumpWrapper;",
        "import org.instrument.Func;",
        "import org.instrument.VoidFunc;"
    ]
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
    
    # Re-find methods after adding imports
    while stack:
        n = stack.pop()
        if n.type in ("method_declaration", "constructor_declaration"):
            sig = method_signature_from_node(src, n)
            if sig in target_signatures:
                method_nodes.append(n)
        for i in range(n.child_count):
            stack.append(n.child(i))

    # Sort by start position (reverse order for safe replacement)
    method_nodes.sort(key=lambda n: n.start_byte, reverse=True)
    
    new_src = bytearray(src)
    
    for method_node in method_nodes:
        # Get method details BEFORE modifying the source
        method_name_node = method_node.child_by_field_name("name")
        method_name = src[method_name_node.start_byte:method_name_node.end_byte].decode("utf-8")
        
        params_node = method_node.child_by_field_name("parameters")
        params_text = src[params_node.start_byte:params_node.end_byte].decode("utf-8") if params_node else "()"
        
        # Extract parameter names
        param_names = []
        if params_text and len(params_text) >= 2:
            inside = params_text[1:-1].strip()
            if inside:
                for part in inside.split(','):
                    name = part.strip().split()[-1]
                    name = name.replace("...", "").replace("@", "").strip()
                    name = name.replace(")", "").replace("(", "")
                    if name:
                        param_names.append(name)
        
        # Check if static method
        is_static = False
        for i in range(method_node.child_count):
            child = method_node.child(i)
            if child.type == "modifiers":
                text_slice = src[child.start_byte:child.end_byte].decode("utf-8")
                if "static" in text_slice.split():
                    is_static = True
                    break
        
        # Check if constructor
        is_constructor = (method_node.type == "constructor_declaration")
        
        # Get method body
        body = method_node.child_by_field_name("body")
        if body is None or body.type not in ("block", "constructor_body"):
            continue
            
        body_start = body.start_byte
        body_end = body.end_byte
        inner = src[body_start:body_end]  # Use original src for body content
        
        # Add @DumpObj annotation AFTER getting all the details
        insert_at = method_node.start_byte
        annotation_added = False
        if b"@DumpObj" not in new_src[max(0, insert_at - 100):insert_at]:
            new_src[insert_at:insert_at] = b"\n@DumpObj\n"
            annotation_added = True
            # Adjust body positions if annotation was added
            if annotation_added:
                body_start += len(b"\n@DumpObj\n")
                body_end += len(b"\n@DumpObj\n")
        
        if not inner or inner[0] != ord('{') or inner[-1] != ord('}'):
            continue
        
        # Before modifying non-constructor methods, normalize throws clause to 'throws Exception'
        # so that the anonymous wrapper (which throws Exception) doesn't cause unreported exceptions.
        if not is_constructor:
            header_start = method_node.start_byte
            header_end = body_start
            header_bytes = bytes(new_src[header_start:header_end])
            # Separate trailing whitespace before '{' to preserve formatting
            stripped = header_bytes.rstrip()
            trailing_ws_len = len(header_bytes) - len(stripped)
            prefix = stripped
            suffix_ws = header_bytes[len(stripped):]
            throws_idx = prefix.find(b"throws ")
            if throws_idx != -1:
                # Replace existing throws list with 'throws Exception '
                new_prefix = prefix[:throws_idx] + b"throws Exception "
                new_header = new_prefix + suffix_ws
            else:
                # Insert ' throws Exception' before any trailing whitespace
                new_header = prefix + b" throws Exception" + suffix_ws
            if new_header != header_bytes:
                # Apply header edit and adjust body offsets
                delta = len(new_header) - len(header_bytes)
                new_src[header_start:header_end] = new_header
                body_start += delta
                body_end += delta

        # Extract original method content
        content = inner[1:-1]  # Remove { and }
        
        # Handle constructors with super()/this() calls
        header_stmt = b""
        rest_content = content
        if is_constructor:
            semi_idx = content.find(b";")
            if semi_idx != -1:
                first_stmt = content[:semi_idx + 1]
                if b"super(" in first_stmt or b"this(" in first_stmt:
                    header_stmt = first_stmt + b"\n"
                    rest_content = content[semi_idx + 1:]
        
        # Create parameter array
        param_array = b"new Object[]{" + b", ".join([name.encode("utf-8") for name in param_names]) + b"}" if param_names else b"new Object[]{}"
        
        # Determine self expression
        self_expr = b"null" if is_static else b"this"
        
        # Create wrapper call
        if is_constructor:
            # For constructors, inject inline try/finally logging after any leading super/this call.
            # Build parameter map inline to avoid changing throws or using anonymous classes.
            id_decl = b"String __objdump_id = org.instrument.DebugDump.newInvocationId();\n"
            map_decl = b"java.util.Map<String,Object> __objdump_params = new java.util.LinkedHashMap<String,Object>();\n"
            # Fill parameter map
            if param_names:
                puts = b"".join([
                    b"__objdump_params.put(\"param" + str(i).encode("utf-8") + b"\", " + name.encode("utf-8") + b");\n"
                    for i, name in enumerate(param_names)
                ])
            else:
                puts = b""
            entry_call = b"org.instrument.DebugDump.writeEntry(this, __objdump_params, __objdump_id);\n"
            # Body content after header
            body_after_header = rest_content if header_stmt else content
            try_finally = (
                b"try {\n" + body_after_header + b"\n} finally {\n" +
                b"org.instrument.DebugDump.writeExit(this, null, null, __objdump_id);\n" +
                b"}"
            )
            injected = id_decl + map_decl + puts + entry_call + try_finally
            if header_stmt:
                new_body = b"{" + header_stmt + injected + b"\n}"
            else:
                new_body = b"{" + injected + b"\n}"
        else:
            # Check return type
            return_type_node = method_node.child_by_field_name("type")
            is_void_method = False
            
            if return_type_node is not None:
                return_type = src[return_type_node.start_byte:return_type_node.end_byte].decode("utf-8")
                is_void_method = (return_type == "void")
            
            if is_void_method:
                # Void method
                wrapper_call = (
                    b"DumpWrapper.wrapVoid(" + self_expr + b", " + 
                    param_array + b", new VoidFunc() { public void call() throws Exception {\n" + content + b"\n} });"
                )
                new_body = b"{" + wrapper_call + b"\n}"
            else:
                # Method with return value
                return_type = src[return_type_node.start_byte:return_type_node.end_byte]
                wrapper_call = (
                    b"return DumpWrapper.wrap(" + self_expr + b", " + 
                    param_array + b", new Func<" + return_type + b">() { public " + return_type + b" call() throws Exception {\n" + content + b"\n} });"
                )
                new_body = b"{" + wrapper_call + b"\n}"
        
        # Replace method body
        new_src[body_start:body_end] = new_body

    # Write the instrumented file
    with open(java_file, "wb") as f:
        f.write(bytes(new_src))

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