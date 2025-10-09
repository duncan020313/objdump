import os
import tempfile
import shutil
import pytest
from objdump.instrumentation.instrumenter import instrument_java_file


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
        assert "String processData(String input, int count)" in result
        
        # Check that the file was modified
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should contain DumpWrapper import and usage
        assert "import org.instrument.DumpWrapper;" in content
        assert "@DumpObj" in content
        assert "DumpWrapper.wrap(" in content
        assert "Supplier" in content
    
    def test_void_method_instrumentation(self):
        """Test instrumentation of a void method."""
        java_file = self.copy_fixture("Sample.java")
        
        # Instrument the printInfo method
        result = instrument_java_file(java_file, ["void printInfo()"])
        
        assert len(result) == 1
        assert "void printInfo()" in result
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should use wrapVoid for void methods
        assert "DumpWrapper.wrapVoid(" in content
        assert "Runnable" in content
    
    def test_static_method_instrumentation(self):
        """Test instrumentation of static methods."""
        java_file = self.copy_fixture("SampleStatic.java")
        
        # Instrument static methods
        result = instrument_java_file(java_file, [
            "String processStatic(String input, int count)",
            "void printStatic(String message)"
        ])
        
        assert len(result) == 2
        assert "String processStatic(String input, int count)" in result
        assert "void printStatic(String message)" in result
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should use null for self in static methods
        assert "DumpWrapper.wrap(null," in content
        assert "DumpWrapper.wrapVoid(null," in content
    
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
        assert "SampleConstructor()" in result
        assert "SampleConstructor(String name)" in result
        assert "SampleConstructor(String name, int value)" in result
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should use wrapVoid for constructors
        assert "DumpWrapper.wrapVoid(" in content
        # Should preserve super() calls
        assert "super();" in content
    
    def test_constructor_with_this_call(self):
        """Test instrumentation of constructor with this() call."""
        java_file = self.copy_fixture("SampleConstructor.java")
        
        # Instrument the constructor with this() call
        result = instrument_java_file(java_file, ["SampleConstructor(int value)"])
        
        assert len(result) == 1
        assert "SampleConstructor(int value)" in result
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should preserve this() call outside wrapper
        assert "this(" in content
        assert "DumpWrapper.wrapVoid(" in content
    
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
        assert "String processData(String input, int count)" in result
        assert "void printInfo()" in result
        assert "int calculate(int a, int b, int c)" in result
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should have multiple @DumpObj annotations
        assert content.count("@DumpObj") == 3
        # Should have both wrap and wrapVoid calls
        assert "DumpWrapper.wrap(" in content
        assert "DumpWrapper.wrapVoid(" in content
    
    def test_no_matching_methods(self):
        """Test behavior when no methods match the target signatures."""
        java_file = self.copy_fixture("Sample.java")
        
        result = instrument_java_file(java_file, ["String nonExistentMethod()"])
        
        assert len(result) == 0
        
        # File should not be modified
        with open(java_file, 'r') as f:
            content = f.read()
        
        assert "DumpWrapper" not in content
        assert "@DumpObj" not in content
    
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
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should create parameter array with correct names
        assert "new Object[]{input, count}" in content
    
    def test_exception_method_instrumentation(self):
        """Test instrumentation of methods that throw exceptions."""
        java_file = self.copy_fixture("Sample.java")
        
        result = instrument_java_file(java_file, ["void throwException() throws Exception"])
        
        assert len(result) == 1
        assert "void throwException() throws Exception" in result
        
        with open(java_file, 'r') as f:
            content = f.read()
        
        # Should use wrapVoid for void methods that throw exceptions
        assert "DumpWrapper.wrapVoid(" in content
        # Exception handling is automatic in the wrapper
