from typing import Dict, List, Set, Tuple
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")
from tree_sitter import Parser
from tree_sitter_languages import get_language
from instrumentation.ts import method_signature_from_node


def find_return_statements(method_body_node) -> List[Tuple[int, int, str]]:
    """Find all return statements in a method body and return their positions and expressions.
    
    Returns:
        List of (start_byte, end_byte, expression) tuples for each return statement
    """
    returns = []
    
    def traverse(node):
        if node.type == "return_statement":
            # Get the full return statement
            full_start = node.start_byte
            full_end = node.end_byte
            
            # Check if it has an expression (not just 'return;')
            if node.child_count > 1:  # Has expression
                expr_node = node.child(1)  # Skip 'return' keyword
                expr_start = expr_node.start_byte
                expr_end = expr_node.end_byte
                returns.append((full_start, full_end, "expr"))
            else:  # Just 'return;' (void)
                returns.append((full_start, full_end, "void"))
        
        for i in range(node.child_count):
            traverse(node.child(i))
    
    traverse(method_body_node)
    return returns


def transform_returns_with_logging(src: bytes, method_body_node, return_type: str, 
                                 self_expr: bytes, id_var: str, is_void: bool) -> bytes:
    """Transform all return statements in a method body to log exit before returning.
    
    Args:
        src: Original source bytes
        method_body_node: The method body AST node
        return_type: Return type string (e.g., "int", "String", "void")
        self_expr: Expression for 'this' (b"this" or b"null")
        id_var: Variable name for the invocation ID
        is_void: Whether this is a void method
    
    Returns:
        Transformed method body as bytes
    """
    returns = find_return_statements(method_body_node)
    
    if not returns:
        # No explicit returns - add exit log at the end
        body_content = src[method_body_node.start_byte:method_body_node.end_byte]
        if is_void:
            exit_log = b"org.instrument.DebugDump.writeExit(" + self_expr + b", null, null, " + id_var.encode() + b");\n"
            return body_content + exit_log
        else:
            # Non-void method with no explicit returns - add at end
            ret_var = b"__objdump_ret"
            exit_log = return_type.encode('utf-8') + b" " + ret_var + b" = null;\n" + \
                      b"org.instrument.DebugDump.writeExit(" + self_expr + b", null, (Object)" + ret_var + b", " + id_var.encode() + b");\n" + \
                      b"return " + ret_var + b";\n"
            return body_content + exit_log
    
    # Sort returns by position (reverse order for safe replacement)
    returns.sort(key=lambda x: x[0], reverse=True)
    
    new_body = bytearray(src[method_body_node.start_byte:method_body_node.end_byte])
    
    # For non-void methods, declare the return variable once at the beginning
    if not is_void and returns:
        # Use the actual return type instead of Object
        ret_var_decl = return_type.encode('utf-8') + b" __objdump_ret;\n"
        new_body = bytearray(ret_var_decl) + new_body
    
    for i, (start_byte, end_byte, expr_type) in enumerate(returns):
        # Convert to relative positions within the method body
        rel_start = start_byte - method_body_node.start_byte
        rel_end = end_byte - method_body_node.start_byte
        
        # Adjust for the variable declaration we added
        if not is_void and returns:
            rel_start += len(ret_var_decl)
            rel_end += len(ret_var_decl)
        
        if expr_type == "void":
            # void return - just add exit log before return
            exit_log = b"org.instrument.DebugDump.writeExit(" + self_expr + b", null, null, " + id_var.encode() + b");\n"
            new_body[rel_start:rel_end] = exit_log + b"return;"
        else:
            # return with expression - extract expression and transform
            return_content = new_body[rel_start:rel_end].decode('utf-8')
            # Extract expression part (everything after 'return ')
            if return_content.startswith('return '):
                expr_content = return_content[7:].rstrip(';').encode('utf-8')
            else:
                expr_content = return_content.encode('utf-8')
            
            if return_type == "void":
                # This shouldn't happen, but handle gracefully
                exit_log = b"org.instrument.DebugDump.writeExit(" + self_expr + b", null, null, " + id_var.encode() + b");\n"
                new_body[rel_start:rel_end] = exit_log + b"return;"
            else:
                # Non-void return - assign to existing variable and log
                exit_log = b"__objdump_ret = (" + expr_content + b");\n" + \
                          b"org.instrument.DebugDump.writeExit(" + self_expr + b", null, (Object)__objdump_ret, " + id_var.encode() + b");\n" + \
                          b"return __objdump_ret;"
                new_body[rel_start:rel_end] = exit_log
    
    # For void methods, check if we need to add exit log at the end
    if is_void and returns:
        # Check if the method ends with a return statement
        last_return = max(returns, key=lambda x: x[0])
        method_end = len(new_body) - 1
        
        # If the last return is not at the very end, add exit log
        if last_return[0] - method_body_node.start_byte < method_end - 10:  # Some tolerance for whitespace
            exit_log = b"org.instrument.DebugDump.writeExit(" + self_expr + b", null, null, " + id_var.encode() + b");\n"
            new_body.extend(exit_log)
    
    return bytes(new_body)


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
        "import org.instrument.DebugDump;"
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
            
        # Store original body positions before any modifications
        original_body_start = body.start_byte
        original_body_end = body.end_byte
        inner = src[original_body_start:original_body_end]  # Use original src for body content
        
        # Add @DumpObj annotation AFTER getting all the details
        insert_at = method_node.start_byte
        annotation_added = False
        if b"@DumpObj" not in new_src[max(0, insert_at - 100):insert_at]:
            new_src[insert_at:insert_at] = b"\n@DumpObj\n"
            annotation_added = True
        
        # Calculate adjusted body positions after annotation insertion
        body_start = original_body_start
        body_end = original_body_end
        if annotation_added:
            body_start += len(b"\n@DumpObj\n")
            body_end += len(b"\n@DumpObj\n")
        
        if not inner or inner[0] != ord('{') or inner[-1] != ord('}'):
            continue
        
        # For non-constructor methods, preserve existing throws clause to avoid signature conflicts
        # The wrapper methods will handle exceptions internally without changing the method signature
        if not is_constructor:
            # No need to modify throws clause - preserve original method signature
            pass

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
        
        # Create instrumentation with return value capture
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
        
        entry_call = b"org.instrument.DebugDump.writeEntry(" + self_expr + b", __objdump_params, __objdump_id);\n"
        
        if is_constructor:
            # For constructors, handle super/this calls and transform returns
            body_after_header = rest_content if header_stmt else content
            
            # Create a temporary body node for return transformation
            # We need to parse the body content to find return statements
            temp_src = b"class Temp { void method() {" + body_after_header + b"} }"
            temp_tree = parser.parse(temp_src)
            temp_cursor = temp_tree.walk()
            temp_stack = [temp_cursor.node]
            temp_body_node = None
            
            while temp_stack:
                n = temp_stack.pop()
                if n.type == "block":
                    temp_body_node = n
                    break
                for i in range(n.child_count):
                    temp_stack.append(n.child(i))
            
            if temp_body_node:
                # Transform returns in constructor body
                transformed_body = transform_returns_with_logging(temp_src, temp_body_node, "void", b"this", "__objdump_id", True)
                # Remove the class wrapper we added
                transformed_body = transformed_body[1:-1]  # Remove the { } from method body
            else:
                transformed_body = body_after_header
            
            injected = id_decl + map_decl + puts + entry_call + transformed_body
            if header_stmt:
                new_body = b"{" + header_stmt + injected + b"\n}"
            else:
                new_body = b"{" + injected + b"\n}"
        else:
            # Check return type for regular methods
            return_type_node = method_node.child_by_field_name("type")
            is_void_method = False
            return_type = "void"
            
            if return_type_node is not None:
                return_type = src[return_type_node.start_byte:return_type_node.end_byte].decode("utf-8").strip()
                is_void_method = (return_type == "void")
            
            # Transform returns in method body
            transformed_body = transform_returns_with_logging(src, body, return_type, self_expr, "__objdump_id", is_void_method)
            
            new_body = b"{" + id_decl + map_decl + puts + entry_call + transformed_body + b"\n}"
        
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