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

    # Deploy DumpObj.java
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

    # Deploy DebugDump.java
    debug_dump_path = os.path.join(pkg_dir, "DebugDump.java")
    content = _read_java_template("DebugDump.java")
    if not content:
        # Fallback content if template missing
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
            "      Map<String,Object> rec = new LinkedHashMap<String,Object>();\n"
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

    # Deploy DumpWrapper.java
    dump_wrapper_path = os.path.join(pkg_dir, "DumpWrapper.java")
    content = _read_java_template("DumpWrapper.java")
    if not content:
        # Fallback content if template missing
        content = (
            "package org.instrument;\n\n"
            "import java.util.*;\n\n"
            "public final class DumpWrapper {\n"
            "    private DumpWrapper() {}\n"
            "    public static <T> T wrap(Object self, Object[] params, Func<T> method) {\n"
            "        String id = DebugDump.newInvocationId();\n"
            "        Map<String, Object> paramMap = extractParameterMap(params);\n"
            "        DebugDump.writeEntry(self, paramMap, id);\n"
            "        try {\n"
            "            T result = method.call();\n"
            "            DebugDump.writeExit(self, null, result, id);\n"
            "            return result;\n"
            "        } catch (Exception e) {\n"
            "            DebugDump.writeExit(self, null, null, id);\n"
            "            if (e instanceof RuntimeException) {\n"
            "                throw (RuntimeException) e;\n"
            "            } else {\n"
            "                throw new RuntimeException(e);\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "    public static void wrapVoid(Object self, Object[] params, VoidFunc method) {\n"
            "        String id = DebugDump.newInvocationId();\n"
            "        Map<String, Object> paramMap = extractParameterMap(params);\n"
            "        DebugDump.writeEntry(self, paramMap, id);\n"
            "        try {\n"
            "            method.call();\n"
            "            DebugDump.writeExit(self, null, null, id);\n"
            "        } catch (Exception e) {\n"
            "            DebugDump.writeExit(self, null, null, id);\n"
            "            if (e instanceof RuntimeException) {\n"
            "                throw (RuntimeException) e;\n"
            "            } else {\n"
            "                throw new RuntimeException(e);\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "    private static Map<String, Object> extractParameterMap(Object[] params) {\n"
            "        Map<String, Object> paramMap = new LinkedHashMap<String, Object>();\n"
            "        if (params == null || params.length == 0) {\n"
            "            return paramMap;\n"
            "        }\n"
            "        for (int i = 0; i < params.length; i++) {\n"
            "            paramMap.put(\"param\" + i, params[i]);\n"
            "        }\n"
            "        return paramMap;\n"
            "    }\n"
            "    public static Map<String, Object> params(Object... values) {\n"
            "        Map<String, Object> m = new LinkedHashMap<String, Object>();\n"
            "        if (values == null || values.length == 0) {\n"
            "            return m;\n"
            "        }\n"
            "        for (int i = 0; i < values.length; i++) {\n"
            "            m.put(\"param\" + i, values[i]);\n"
            "        }\n"
            "        return m;\n"
            "    }\n"
            "}\n"
        )
    with open(dump_wrapper_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Deploy Func.java
    func_path = os.path.join(pkg_dir, "Func.java")
    if not os.path.isfile(func_path):
        content = _read_java_template("Func.java")
        if not content:
            content = (
                "package org.instrument;\n\n"
                "public interface Func<T> {\n"
                "    T call();\n"
                "}\n"
            )
        with open(func_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Deploy VoidFunc.java
    void_func_path = os.path.join(pkg_dir, "VoidFunc.java")
    if not os.path.isfile(void_func_path):
        content = _read_java_template("VoidFunc.java")
        if not content:
            content = (
                "package org.instrument;\n\n"
                "public interface VoidFunc {\n"
                "    void call();\n"
                "}\n"
            )
        with open(void_func_path, "w", encoding="utf-8") as f:
            f.write(content)


