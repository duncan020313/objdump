import os


def _read_java_template(filename: str) -> str:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(os.path.dirname(base_dir), "java_templates", filename)
        if os.path.isfile(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    return ""


def ensure_helper_sources(work_dir: str, src_java_rel: str) -> None:
    pkg_dir = os.path.join(work_dir, src_java_rel, "org", "instrument")
    os.makedirs(pkg_dir, exist_ok=True)

    dump_obj_path = os.path.join(pkg_dir, "DumpObj.java")
    if not os.path.isfile(dump_obj_path):
        content = _read_java_template("DumpObj.java")
        if not content:
            content = (
                "package org.instrument;\n\n"
                "import java.lang.annotation.*;\n\n"
                "@Retention(RetentionPolicy.RUNTIME)\n"
                "@Target({ElementType.METHOD, ElementType.CONSTRUCTOR})\n"
                "public @interface DumpObj { }\n"
            )
        with open(dump_obj_path, "w", encoding="utf-8") as f:
            f.write(content)

    debug_dump_path = os.path.join(pkg_dir, "DebugDump.java")
    content = _read_java_template("DebugDump.java")
    if not content:
        content = (
            "package org.instrument;\n\n"
            "import com.fasterxml.jackson.databind.ObjectMapper;\n"
            "import java.io.*;\n"
            "import java.util.*;\n\n"
            "public final class DebugDump {\n"
            "  private static final ObjectMapper M = new ObjectMapper();\n"
            "  private DebugDump() {}\n"
            "  public static String newInvocationId() { return UUID.randomUUID().toString(); }\n"
            "  public static void writeEntry(Object self, Map params, String id) { write(self, params, null, id, \"entry\"); }\n"
            "  public static void writeExit(Object self, Map params, Object ret, String id) { write(self, params, ret, id, \"exit\"); }\n"
            "  private static synchronized void write(Object self, Map params, Object ret, String id, String phase) {\n"
            "    try {\n"
            "      Map<String,Object> rec = new LinkedHashMap<>();\n"
            "      rec.put(\"id\", id);\n"
            "      rec.put(\"phase\", phase);\n"
            "      rec.put(\"self\", self);\n"
            "      rec.put(\"params\", params);\n"
            "      rec.put(\"ret\", ret);\n"
            "      String json = M.writeValueAsString(rec);\n"
            "      System.out.println(\"__INSTR__\" + json);\n"
            "    } catch (Exception ignored) { }\n"
            "  }\n"
            "}\n"
        )
    with open(debug_dump_path, "w", encoding="utf-8") as f:
        f.write(content)


