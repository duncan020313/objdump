"""Test that the report format includes JavaDoc and code."""
import os
import json
import tempfile
import shutil
from instrumentation.instrumenter import instrument_changed_methods


def test_report_format_with_javadoc():
    """Test that the report includes file, signature, code, and javadoc fields."""
    test_file = os.path.join(os.path.dirname(__file__), "fixtures", "SampleWithJavaDoc.java")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_copy = os.path.join(tmpdir, "SampleWithJavaDoc.java")
        shutil.copy(test_file, test_copy)
        
        # Create changed_methods dict
        changed_methods = {
            test_copy: [
                "String processData(String input, int count)",
                "String getData()"
            ]
        }
        
        # Instrument the methods
        result = instrument_changed_methods(changed_methods)
        
        assert len(result) == 1
        assert test_copy in result
        
        methods = result[test_copy]
        assert len(methods) == 2
        
        # Check that each method has the required fields
        for method_info in methods:
            assert "signature" in method_info
            assert "code" in method_info
            assert "javadoc" in method_info
            
            # Check code field is populated
            assert method_info["code"] is not None
            assert len(method_info["code"]) > 0
        
        # Check that processData has JavaDoc
        process_data = next(m for m in methods if m["signature"] == "String processData(String input, int count)")
        assert process_data["javadoc"] is not None
        assert "description" in process_data["javadoc"]
        assert "Processes the input string" in process_data["javadoc"]["description"]
        assert "input" in process_data["javadoc"]["params"]
        assert "count" in process_data["javadoc"]["params"]
        assert process_data["javadoc"]["returns"] is not None
        
        # Check that getData has JavaDoc
        get_data = next(m for m in methods if m["signature"] == "String getData()")
        assert get_data["javadoc"] is not None
        assert "Simple getter" in get_data["javadoc"]["description"]


def test_report_format_without_javadoc():
    """Test that methods without JavaDoc have javadoc field as None."""
    test_file = os.path.join(os.path.dirname(__file__), "fixtures", "SampleWithJavaDoc.java")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_copy = os.path.join(tmpdir, "SampleWithJavaDoc.java")
        shutil.copy(test_file, test_copy)
        
        # Create changed_methods dict with setData (no JavaDoc)
        changed_methods = {
            test_copy: ["void setData(String data)"]
        }
        
        # Instrument the methods
        result = instrument_changed_methods(changed_methods)
        
        assert len(result) == 1
        assert test_copy in result
        
        methods = result[test_copy]
        assert len(methods) == 1
        
        set_data = methods[0]
        assert set_data["signature"] == "void setData(String data)"
        assert set_data["code"] is not None
        assert set_data["javadoc"] is None


def test_report_json_serializable():
    """Test that the report data is JSON serializable."""
    test_file = os.path.join(os.path.dirname(__file__), "fixtures", "SampleWithJavaDoc.java")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_copy = os.path.join(tmpdir, "SampleWithJavaDoc.java")
        shutil.copy(test_file, test_copy)
        
        # Create changed_methods dict
        changed_methods = {
            test_copy: ["String processData(String input, int count)"]
        }
        
        # Instrument the methods
        result = instrument_changed_methods(changed_methods)
        
        # Build report items as done in project.py
        report_items = []
        for fpath, method_infos in result.items():
            abs_path = os.path.abspath(fpath)
            for method_info in method_infos:
                report_items.append({
                    "file": abs_path,
                    "signature": method_info["signature"],
                    "code": method_info["code"],
                    "javadoc": method_info["javadoc"]
                })
        
        # Try to serialize to JSON
        json_str = json.dumps(report_items, indent=2, ensure_ascii=False)
        
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert len(parsed) == 1
        assert parsed[0]["signature"] == "String processData(String input, int count)"
        assert parsed[0]["javadoc"] is not None

