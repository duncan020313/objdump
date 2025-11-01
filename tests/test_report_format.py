"""Test that the report format includes JavaDoc and code."""
import os
import json
import subprocess
import tempfile
import textwrap
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
            assert "relevant_methods" in method_info
            assert isinstance(method_info["relevant_methods"], list)

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
        assert set_data["relevant_methods"] == []


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
                    "javadoc": method_info["javadoc"],
                    "relevant_methods": method_info.get("relevant_methods", [])
                })

        # Try to serialize to JSON
        json_str = json.dumps(report_items, indent=2, ensure_ascii=False)

        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert len(parsed) == 1
        assert parsed[0]["signature"] == "String processData(String input, int count)"
        assert parsed[0]["javadoc"] is not None
        assert "relevant_methods" in parsed[0]
        assert isinstance(parsed[0]["relevant_methods"], list)


def test_debug_dump_field_filter_runtime():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    debug_dump_src = os.path.join(root_dir, "java_templates", "DebugDump.java")

    with tempfile.TemporaryDirectory() as tmpdir:
        org_dir = os.path.join(tmpdir, "org", "instrument")
        os.makedirs(org_dir, exist_ok=True)

        shutil.copy2(debug_dump_src, os.path.join(org_dir, "DebugDump.java"))

        harness_source = textwrap.dedent(
            """
            package org.instrument;

            import java.util.Arrays;
            import java.util.LinkedHashMap;
            import java.util.List;
            import java.util.Map;

            public final class DebugDumpHarness {
                private DebugDumpHarness() { }

                public static void main(String[] args) {
                    SampleObject self = new SampleObject();
                    self.name = "self-name";
                    self.meta = new Nested();
                    self.meta.secret = "hidden";

                    ParamsObject param = new ParamsObject();
                    param.a = 42;
                    param.nested = new Nested();
                    param.nested.secret = "param-secret";

                    Map<String, Object> params = new LinkedHashMap<String, Object>();
                    params.put("param", param);

                    Map<String, List<String>> filter = new LinkedHashMap<String, List<String>>();
                    filter.put("_self", Arrays.asList("name"));
                    filter.put("param", Arrays.asList("nested.secret"));

                    DebugDump.writeEntry(self, params, "id", "sig", "file", filter);
                }

                static final class SampleObject {
                    String name;
                    Nested meta;
                }

                static final class Nested {
                    String secret;
                }

                static final class ParamsObject {
                    int a;
                    Nested nested;
                }
            }
            """
        ).strip()

        harness_path = os.path.join(org_dir, "DebugDumpHarness.java")
        with open(harness_path, "w", encoding="utf-8") as fh:
            fh.write(harness_source)

        compile_cmd = [
            "javac",
            "org/instrument/DebugDump.java",
            "org/instrument/DebugDumpHarness.java",
        ]
        subprocess.run(compile_cmd, cwd=tmpdir, check=True)

        out_path = os.path.join(tmpdir, "filtered.out")
        env = os.environ.copy()
        env["OBJDUMP_OUT"] = out_path

        subprocess.run(["java", "org.instrument.DebugDumpHarness"], cwd=tmpdir, env=env, check=True)

        with open(out_path, "r", encoding="utf-8") as fh:
            records = json.load(fh)

        assert isinstance(records, list)
        assert len(records) == 1

        record = records[0]
        self_obj = record["self"]
        params_obj = record["params"]["param"]

        assert self_obj["name"] == "self-name"
        assert "meta" not in self_obj
        assert record["ret"] is None

        assert "a" not in params_obj
        assert "nested" in params_obj
        nested_obj = params_obj["nested"]
        assert nested_obj["secret"] == "param-secret"

