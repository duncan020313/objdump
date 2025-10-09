package org.instrument;

import java.util.*;

public final class DumpWrapper {
    private DumpWrapper() {}

    /**
     * Wrap a method with return value using DumpWrapper
     */
    public static <T> T wrap(Object self, Object[] params, Func<T> method) throws Exception {
        String id = DebugDump.newInvocationId();
        Map<String, Object> paramMap = extractParameterMap(params);
        
        DebugDump.writeEntry(self, paramMap, id);
        try {
            T result = method.call();
            DebugDump.writeExit(self, null, result, id);
            return result;
        } catch (Exception e) {
            DebugDump.writeExit(self, null, null, id);
            throw e;
        }
    }

    /**
     * Wrap a void method using DumpWrapper
     */
    public static void wrapVoid(Object self, Object[] params, VoidFunc method) throws Exception {
        String id = DebugDump.newInvocationId();
        Map<String, Object> paramMap = extractParameterMap(params);
        
        DebugDump.writeEntry(self, paramMap, id);
        try {
            method.call();
            DebugDump.writeExit(self, null, null, id);
        } catch (Exception e) {
            DebugDump.writeExit(self, null, null, id);
            throw e;
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
}
