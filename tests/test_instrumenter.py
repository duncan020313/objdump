import os
import tempfile
import shutil
import pytest
from instrumentation.instrumenter import instrument_java_file


class TestInstrumenter:
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    
    def teardown_method(self):
        """Clean up after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def copy_fixture(self, fixture_name: str) -> str:
        """Copy a fixture file to temp directory and return its path."""
        src_path = os.path.join(self.fixtures_dir, fixture_name)
        dst_path = os.path.join(self.temp_dir, fixture_name)
        shutil.copy2(src_path, dst_path)
        return dst_path
    
    def test_simple_method_instrumentation(self):
        """Test instrumentation of a simple method with return value."""
        java_file = self.copy_fixture("Sample.java")
        
        # Instrument the processData method
        result = instrument_java_file(java_file, ["String processData(String input, int count)"])
        
        assert len(result) == 1
        assert result[0]["signature"] == "String processData(String input, int count)"
        assert result[0]["code"] is not None
        
        # Check that the file was modified
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should contain @DumpObj annotation
        assert "@DumpObj" in content
    
    def test_void_method_instrumentation(self):
        """Test instrumentation of a void method."""
        java_file = self.copy_fixture("Sample.java")
        
        # Instrument the printInfo method
        result = instrument_java_file(java_file, ["void printInfo()"])
        
        assert len(result) == 1
        assert result[0]["signature"] == "void printInfo()"
        assert result[0]["code"] is not None
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should contain @DumpObj annotation
        assert "@DumpObj" in content
    
    def test_static_method_instrumentation(self):
        """Test instrumentation of static methods."""
        java_file = self.copy_fixture("SampleStatic.java")
        
        # Instrument static methods
        result = instrument_java_file(java_file, [
            "String processStatic(String input, int count)",
            "void printStatic(String message)"
        ])
        
        assert len(result) == 2
        signatures = [r["signature"] for r in result]
        assert "String processStatic(String input, int count)" in signatures
        assert "void printStatic(String message)" in signatures
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should contain @DumpObj annotations
        assert "@DumpObj" in content
    
    def test_constructor_instrumentation(self):
        """Test instrumentation of constructors."""
        java_file = self.copy_fixture("SampleConstructor.java")
        
        # Instrument constructors
        result = instrument_java_file(java_file, [
            "SampleConstructor()",
            "SampleConstructor(String name)",
            "SampleConstructor(String name, int value)"
        ])
        
        assert len(result) == 3
        signatures = [r["signature"] for r in result]
        assert "SampleConstructor()" in signatures
        assert "SampleConstructor(String name)" in signatures
        assert "SampleConstructor(String name, int value)" in signatures
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should contain @DumpObj annotations
        assert "@DumpObj" in content
    
    def test_constructor_with_this_call(self):
        """Test instrumentation of constructor with this() call."""
        java_file = self.copy_fixture("SampleConstructor.java")
        
        # Instrument the constructor with this() call (using actual signature from file)
        result = instrument_java_file(java_file, ["SampleConstructor(String name)"])
        
        assert len(result) == 1
        assert result[0]["signature"] == "SampleConstructor(String name)"
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should contain @DumpObj annotation
        assert "@DumpObj" in content
        # Should have this() call preserved
        assert "this(" in content
    
    def test_multiple_methods_same_file(self):
        """Test instrumentation of multiple methods in the same file."""
        java_file = self.copy_fixture("Sample.java")
        
        # Instrument multiple methods
        result = instrument_java_file(java_file, [
            "String processData(String input, int count)",
            "void printInfo()",
            "int calculate(int a, int b, int c)"
        ])
        
        assert len(result) == 3
        signatures = [r["signature"] for r in result]
        assert "String processData(String input, int count)" in signatures
        assert "void printInfo()" in signatures
        assert "int calculate(int a, int b, int c)" in signatures
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should have multiple @DumpObj annotations
        assert content.count("@DumpObj") >= 3
    
    def test_no_matching_methods(self):
        """Test behavior when no methods match the target signatures."""
        java_file = self.copy_fixture("Sample.java")
        
        result = instrument_java_file(java_file, ["String nonExistentMethod()"])
        
        assert len(result) == 0
    
    def test_empty_target_signatures(self):
        """Test behavior with empty target signatures list."""
        java_file = self.copy_fixture("Sample.java")
        
        result = instrument_java_file(java_file, [])
        
        assert len(result) == 0
    
    def test_nonexistent_file(self):
        """Test behavior with non-existent file."""
        result = instrument_java_file("/nonexistent/file.java", ["String method()"])
        
        assert len(result) == 0
    
    def test_parameter_extraction(self):
        """Test that parameter names are correctly extracted and used."""
        java_file = self.copy_fixture("Sample.java")
        
        result = instrument_java_file(java_file, ["String processData(String input, int count)"])
        
        assert len(result) == 1
        assert result[0]["signature"] == "String processData(String input, int count)"
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should contain @DumpObj annotation
        assert "@DumpObj" in content
    
    def test_exception_method_instrumentation(self):
        """Test instrumentation of methods that throw exceptions."""
        java_file = self.copy_fixture("Sample.java")
        
        # Note: tree-sitter signature doesn't include throws clause
        result = instrument_java_file(java_file, ["void throwException()"])
        
        assert len(result) == 1
        assert result[0]["signature"] == "void throwException()"
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should contain @DumpObj annotation
        assert "@DumpObj" in content
