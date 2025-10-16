"""Tests for JavaDoc extraction functionality."""
import os
from instrumentation.javadoc import extract_javadoc_from_node, parse_javadoc, extract_method_code
from instrumentation.instrumenter import instrument_java_file
from tree_sitter import Parser
from tree_sitter_languages import get_language


def test_extract_javadoc():
    """Test extracting JavaDoc from a method node."""
    test_file = os.path.join(os.path.dirname(__file__), "fixtures", "SampleWithJavaDoc.java")
    
    with open(test_file, "rb") as f:
        src = f.read()
    
    language = get_language("java")
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(src)
    
    # Find the processData method
    cursor = tree.walk()
    stack = [cursor.node]
    process_data_node = None
    
    while stack:
        node = stack.pop()
        if node.type == "method_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                method_name = src[name_node.start_byte:name_node.end_byte].decode("utf-8")
                if method_name == "processData":
                    process_data_node = node
                    break
        for i in range(node.child_count):
            stack.append(node.child(i))
    
    assert process_data_node is not None, "processData method not found"
    
    # Extract JavaDoc
    javadoc_text = extract_javadoc_from_node(src, process_data_node)
    assert javadoc_text is not None, "JavaDoc should be found"
    assert "Processes the input string" in javadoc_text
    
    # Parse JavaDoc
    parsed = parse_javadoc(javadoc_text)
    assert parsed is not None
    assert "Processes the input string" in parsed["description"]
    assert "input" in parsed["params"]
    assert "count" in parsed["params"]
    assert parsed["returns"] is not None
    assert "IllegalArgumentException" in parsed["throws"]


def test_extract_method_without_javadoc():
    """Test extracting JavaDoc from a method without JavaDoc."""
    test_file = os.path.join(os.path.dirname(__file__), "fixtures", "SampleWithJavaDoc.java")
    
    with open(test_file, "rb") as f:
        src = f.read()
    
    language = get_language("java")
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(src)
    
    # Find the setData method (no JavaDoc)
    cursor = tree.walk()
    stack = [cursor.node]
    set_data_node = None
    
    while stack:
        node = stack.pop()
        if node.type == "method_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                method_name = src[name_node.start_byte:name_node.end_byte].decode("utf-8")
                if method_name == "setData":
                    set_data_node = node
                    break
        for i in range(node.child_count):
            stack.append(node.child(i))
    
    assert set_data_node is not None, "setData method not found"
    
    # Extract JavaDoc (should be None)
    javadoc_text = extract_javadoc_from_node(src, set_data_node)
    assert javadoc_text is None, "JavaDoc should not be found for setData"
    
    # Parse JavaDoc (should return None)
    parsed = parse_javadoc(javadoc_text)
    assert parsed is None


def test_extract_method_code():
    """Test extracting method source code."""
    test_file = os.path.join(os.path.dirname(__file__), "fixtures", "SampleWithJavaDoc.java")
    
    with open(test_file, "rb") as f:
        src = f.read()
    
    language = get_language("java")
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(src)
    
    # Find the getData method
    cursor = tree.walk()
    stack = [cursor.node]
    get_data_node = None
    
    while stack:
        node = stack.pop()
        if node.type == "method_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                method_name = src[name_node.start_byte:name_node.end_byte].decode("utf-8")
                if method_name == "getData":
                    get_data_node = node
                    break
        for i in range(node.child_count):
            stack.append(node.child(i))
    
    assert get_data_node is not None, "getData method not found"
    
    # Extract method code
    code = extract_method_code(src, get_data_node)
    assert "public String getData()" in code
    assert "return data;" in code


def test_instrument_java_file_with_javadoc():
    """Test that instrument_java_file returns JavaDoc and code information."""
    test_file = os.path.join(os.path.dirname(__file__), "fixtures", "SampleWithJavaDoc.java")
    
    # Make a copy to avoid modifying the original
    import shutil
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_copy = os.path.join(tmpdir, "SampleWithJavaDoc.java")
        shutil.copy(test_file, test_copy)
        
        # Instrument with all methods
        result = instrument_java_file(test_copy, ["String processData(String input, int count)"])
        
        assert len(result) == 1
        method_info = result[0]
        
        assert method_info["signature"] == "String processData(String input, int count)"
        assert method_info["code"] is not None
        assert "public String processData" in method_info["code"]
        
        assert method_info["javadoc"] is not None
        assert "Processes the input string" in method_info["javadoc"]["description"]
        assert "input" in method_info["javadoc"]["params"]
        assert "count" in method_info["javadoc"]["params"]

