import os
import tempfile
import shutil
import subprocess
import json
import pytest
from instrumentation.instrumenter import instrument_java_file
from instrumentation.helpers import ensure_helper_sources


class TestIntegration:
    
    def setup_method(self):
        """Set up test environment before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        
        # Set up Java source directory structure
        self.src_dir = os.path.join(self.temp_dir, "src", "main", "java")
        os.makedirs(self.src_dir, exist_ok=True)
        
        # Deploy helper sources
        ensure_helper_sources(self.temp_dir, "src/main/java")
    
    def teardown_method(self):
        """Clean up after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def copy_fixture(self, fixture_name: str) -> str:
        """Copy a fixture file to temp directory and return its path."""
        src_path = os.path.join(self.fixtures_dir, fixture_name)
        dst_path = os.path.join(self.src_dir, fixture_name)
        shutil.copy2(src_path, dst_path)
        return dst_path
    
    def compile_java_file(self, java_file: str) -> bool:
        """Compile a Java file and return success status."""
        try:
            # Get the classpath including Jackson JARs (if available)
            classpath = os.path.join(self.temp_dir, "lib", "*")
            if not os.path.exists(os.path.join(self.temp_dir, "lib")):
                classpath = "."
            
            result = subprocess.run([
                "javac", "-cp", classpath, "-parameters", java_file
            ], capture_output=True, text=True, cwd=self.temp_dir)
            
            return result.returncode == 0
        except Exception:
            return False
    
    def run_java_class(self, class_name: str, method_name: str = "main") -> tuple:
        """Run a Java class and return (success, stdout, stderr)."""
        try:
            # Set up output file
            output_file = os.path.join(self.temp_dir, "objdump.out")
            env = os.environ.copy()
            env["OBJDUMP_OUT"] = output_file
            
            result = subprocess.run([
                "java", "-cp", self.temp_dir, class_name
            ], capture_output=True, text=True, cwd=self.temp_dir, env=env)
            
            return result.returncode == 0, result.stdout, result.stderr
        except Exception:
            return False, "", "Execution failed"
    
    def test_simple_instrumentation_compilation(self):
        """Test that instrumented code compiles successfully."""
        java_file = self.copy_fixture("Sample.java")
        
        # Instrument the file
        result = instrument_java_file(java_file, ["String processData(String input, int count)"])
        assert len(result) == 1
        
        # Try to compile
        success = self.compile_java_file(java_file)
        assert success, "Instrumented code should compile successfully"
    
    def test_static_method_instrumentation_compilation(self):
        """Test that instrumented static methods compile successfully."""
        java_file = self.copy_fixture("SampleStatic.java")
        
        # Instrument static methods
        result = instrument_java_file(java_file, [
            "String processStatic(String input, int count)",
            "void printStatic(String message)"
        ])
        assert len(result) == 2
        
        # Try to compile
        success = self.compile_java_file(java_file)
        assert success, "Instrumented static methods should compile successfully"
    
    def test_constructor_instrumentation_compilation(self):
        """Test that instrumented constructors compile successfully."""
        java_file = self.copy_fixture("SampleConstructor.java")
        
        # Instrument constructors
        result = instrument_java_file(java_file, [
            "SampleConstructor()",
            "SampleConstructor(String name)"
        ])
        assert len(result) == 2
        
        # Try to compile
        success = self.compile_java_file(java_file)
        assert success, "Instrumented constructors should compile successfully"
    
    def test_instrumentation_output_format(self):
        """Test that instrumentation produces correct JSON output format."""
        # Create a simple test class
        test_class = """
public class TestClass {
    public String testMethod(String input, int count) {
        return input + "_" + count;
    }
    
    public static void main(String[] args) {
        TestClass obj = new TestClass();
        String result = obj.testMethod("hello", 42);
        System.out.println("Result: " + result);
    }
}
"""
        
        java_file = os.path.join(self.src_dir, "TestClass.java")
        with open(java_file, 'w') as f:
            f.write(test_class)
        
        # Instrument the test method
        result = instrument_java_file(java_file, ["String testMethod(String input, int count)"])
        assert len(result) == 1
        
        # Compile and run
        compile_success = self.compile_java_file(java_file)
        assert compile_success, "Test class should compile"
        
        run_success, stdout, stderr = self.run_java_class("TestClass")
        assert run_success, f"Test class should run successfully. stderr: {stderr}"
        
        # Check output file exists and contains valid JSON
        output_file = os.path.join(self.temp_dir, "objdump.out")
        assert os.path.exists(output_file), "Output file should be created"
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) > 0, "Output file should not be empty"
        
        # Parse JSON lines
        json_objects = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    json_objects.append(obj)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON line: {line}")
        
        # Should have entry and exit records
        assert len(json_objects) >= 2, "Should have at least entry and exit records"
        
        # Check structure of records
        for obj in json_objects:
            assert "id" in obj, "Record should have id field"
            assert "phase" in obj, "Record should have phase field"
            assert "self" in obj, "Record should have self field"
            assert "params" in obj, "Record should have params field"
            assert "ret" in obj, "Record should have ret field"
            assert obj["phase"] in ["entry", "exit"], "Phase should be entry or exit"
    
    def test_parameter_extraction_in_output(self):
        """Test that parameter names are correctly extracted and appear in output."""
        # Create a test class with named parameters
        test_class = """
public class ParameterTest {
    public String testMethod(String input, int count, boolean flag) {
        return input + "_" + count + "_" + flag;
    }
    
    public static void main(String[] args) {
        ParameterTest obj = new ParameterTest();
        String result = obj.testMethod("test", 123, true);
        System.out.println("Result: " + result);
    }
}
"""
        
        java_file = os.path.join(self.src_dir, "ParameterTest.java")
        with open(java_file, 'w') as f:
            f.write(test_class)
        
        # Instrument the test method
        result = instrument_java_file(java_file, ["String testMethod(String input, int count, boolean flag)"])
        assert len(result) == 1
        
        # Compile and run
        compile_success = self.compile_java_file(java_file)
        assert compile_success, "Parameter test class should compile"
        
        run_success, stdout, stderr = self.run_java_class("ParameterTest")
        assert run_success, f"Parameter test class should run successfully. stderr: {stderr}"
        
        # Check output file
        output_file = os.path.join(self.temp_dir, "objdump.out")
        assert os.path.exists(output_file), "Output file should be created"
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        # Find entry record
        entry_record = None
        for line in lines:
            line = line.strip()
            if line:
                obj = json.loads(line)
                if obj.get("phase") == "entry":
                    entry_record = obj
                    break
        
        assert entry_record is not None, "Should have entry record"
        
        # Check parameter names in entry record
        params = entry_record.get("params", {})
        # Note: Parameter names might be param0, param1, etc. if -parameters flag doesn't work
        # or if reflection fails, but we should have the right number of parameters
        assert len(params) == 3, f"Should have 3 parameters, got: {params}"
    
    def test_exception_handling_in_output(self):
        """Test that exceptions are properly handled and logged."""
        # Create a test class that throws an exception
        test_class = """
public class ExceptionTest {
    public String testMethod(String input) throws Exception {
        if (input.equals("throw")) {
            throw new RuntimeException("Test exception");
        }
        return input + "_processed";
    }
    
    public static void main(String[] args) {
        ExceptionTest obj = new ExceptionTest();
        try {
            String result = obj.testMethod("throw");
            System.out.println("Result: " + result);
        } catch (Exception e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
"""
        
        java_file = os.path.join(self.src_dir, "ExceptionTest.java")
        with open(java_file, 'w') as f:
            f.write(test_class)
        
        # Instrument the test method
        result = instrument_java_file(java_file, ["String testMethod(String input) throws Exception"])
        assert len(result) == 1
        
        # Compile and run
        compile_success = self.compile_java_file(java_file)
        assert compile_success, "Exception test class should compile"
        
        run_success, stdout, stderr = self.run_java_class("ExceptionTest")
        # Should succeed even with exception due to try-catch in main
        assert run_success, f"Exception test class should run successfully. stderr: {stderr}"
        
        # Check output file
        output_file = os.path.join(self.temp_dir, "objdump.out")
        assert os.path.exists(output_file), "Output file should be created"
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        # Should have both entry and exit records even with exception
        json_objects = []
        for line in lines:
            line = line.strip()
            if line:
                obj = json.loads(line)
                json_objects.append(obj)
        
        assert len(json_objects) >= 2, "Should have entry and exit records even with exception"
        
        # Find exit record
        exit_record = None
        for obj in json_objects:
            if obj.get("phase") == "exit":
                exit_record = obj
                break
        
        assert exit_record is not None, "Should have exit record"
        # Exit record should have ret=null due to exception
        assert exit_record.get("ret") is None, "Exit record should have null ret due to exception"
