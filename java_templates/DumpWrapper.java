package org.instrument;

import java.util.*;

public final class DumpWrapper {
    private DumpWrapper() {}

    /**
     * Wrap a method with return value using DumpWrapper
     */
    public static <T> T wrap(Object self, Object[] params, Func<T> method) {
        String id = DebugDump.newInvocationId();
        Map<String, Object> paramMap = extractParameterMap(params);
        
        DebugDump.writeEntry(self, paramMap, id, "[DumpWrapper]", "[DumpWrapper]");
        try {
            T result = method.call();
            DebugDump.writeExit(self, null, result, id, "[DumpWrapper]", "[DumpWrapper]");
            return result;
        } catch (Exception e) {
            DebugDump.writeExit(self, null, null, id, "[DumpWrapper]", "[DumpWrapper]");
            // Re-throw as RuntimeException to avoid changing method signatures
            if (e instanceof RuntimeException) {
                throw (RuntimeException) e;
            } else {
                throw new RuntimeException(e);
            }
        }
    }

    /**
     * Wrap a method with return value using DumpWrapper with parameter names
     */
    public static <T> T wrap(Object self, String[] paramNames, Object[] params, Func<T> method) {
        String id = DebugDump.newInvocationId();
        Map<String, Object> paramMap = extractParameterMapWithNames(paramNames, params);
        
        DebugDump.writeEntry(self, paramMap, id, "[DumpWrapper]", "[DumpWrapper]");
        try {
            T result = method.call();
            DebugDump.writeExit(self, null, result, id, "[DumpWrapper]", "[DumpWrapper]");
            return result;
        } catch (Exception e) {
            DebugDump.writeExit(self, null, null, id, "[DumpWrapper]", "[DumpWrapper]");
            // Re-throw as RuntimeException to avoid changing method signatures
            if (e instanceof RuntimeException) {
                throw (RuntimeException) e;
            } else {
                throw new RuntimeException(e);
            }
        }
    }

    /**
     * Wrap a void method using DumpWrapper
     */
    public static void wrapVoid(Object self, Object[] params, VoidFunc method) {
        String id = DebugDump.newInvocationId();
        Map<String, Object> paramMap = extractParameterMap(params);
        
        DebugDump.writeEntry(self, paramMap, id, "[DumpWrapper]", "[DumpWrapper]");
        try {
            method.call();
            DebugDump.writeExit(self, null, null, id, "[DumpWrapper]", "[DumpWrapper]");
        } catch (Exception e) {
            DebugDump.writeExit(self, null, null, id, "[DumpWrapper]", "[DumpWrapper]");
            // Re-throw as RuntimeException to avoid changing method signatures
            if (e instanceof RuntimeException) {
                throw (RuntimeException) e;
            } else {
                throw new RuntimeException(e);
            }
        }
    }

    /**
     * Wrap a void method using DumpWrapper with parameter names
     */
    public static void wrapVoid(Object self, String[] paramNames, Object[] params, VoidFunc method) {
        String id = DebugDump.newInvocationId();
        Map<String, Object> paramMap = extractParameterMapWithNames(paramNames, params);
        
        DebugDump.writeEntry(self, paramMap, id, "[DumpWrapper]", "[DumpWrapper]");
        try {
            method.call();
            DebugDump.writeExit(self, null, null, id, "[DumpWrapper]", "[DumpWrapper]");
        } catch (Exception e) {
            DebugDump.writeExit(self, null, null, id, "[DumpWrapper]", "[DumpWrapper]");
            // Re-throw as RuntimeException to avoid changing method signatures
            if (e instanceof RuntimeException) {
                throw (RuntimeException) e;
            } else {
                throw new RuntimeException(e);
            }
        }
    }

    private static Map<String, Object> extractParameterMap(Object[] params) {
        Map<String, Object> paramMap = new LinkedHashMap<String, Object>();
        
        if (params == null || params.length == 0) {
            return paramMap;
        }
        // Java 6 compatible: we don't rely on reflection Parameter API
        for (int i = 0; i < params.length; i++) {
            paramMap.put("param" + i, params[i]);
        }

        return paramMap;
    }

    private static Map<String, Object> extractParameterMapWithNames(String[] paramNames, Object[] params) {
        Map<String, Object> paramMap = new LinkedHashMap<String, Object>();
        
        if (params == null || params.length == 0) {
            return paramMap;
        }
        
        // Use provided parameter names, fallback to param0, param1, etc. if names not available
        for (int i = 0; i < params.length; i++) {
            String paramName = (paramNames != null && i < paramNames.length && paramNames[i] != null) 
                ? paramNames[i] 
                : "param" + i;
            paramMap.put(paramName, params[i]);
        }

        return paramMap;
    }

    /**
     * Build a parameter map with keys param0..paramN for constructor/method args
     */
    public static Map<String, Object> params(Object... values) {
        Map<String, Object> m = new LinkedHashMap<String, Object>();
        if (values == null || values.length == 0) {
            return m;
        }
        for (int i = 0; i < values.length; i++) {
            m.put("param" + i, values[i]);
        }
        return m;
    }

    /**
     * Build a parameter map with actual parameter names
     */
    public static Map<String, Object> paramsWithNames(String[] paramNames, Object... values) {
        Map<String, Object> m = new LinkedHashMap<String, Object>();
        if (values == null || values.length == 0) {
            return m;
        }
        for (int i = 0; i < values.length; i++) {
            String paramName = (paramNames != null && i < paramNames.length && paramNames[i] != null) 
                ? paramNames[i] 
                : "param" + i;
            m.put(paramName, values[i]);
        }
        return m;
    }
}
