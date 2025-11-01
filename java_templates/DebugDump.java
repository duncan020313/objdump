package org.instrument;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

public final class DebugDump {

  private DebugDump() {}

  public static String newInvocationId() {
    return UUID.randomUUID().toString();
  }

  public static void writeEntry(Object self, Map<String, Object> params, String id, String methodSig, String filePath) {
    writeEntry(self, params, id, methodSig, filePath, null);
  }

  public static void writeEntry(Object self, Map<String, Object> params, String id, String methodSig, String filePath, Map<String, List<String>> fieldFilter) {
    write(self, params, null, id, "entry", methodSig, filePath, fieldFilter);
  }

  public static void writeExit(Object self, Map<String, Object> params, Object ret, String id, String methodSig, String filePath) {
    writeExit(self, params, ret, id, methodSig, filePath, null);
  }

  public static void writeExit(Object self, Map<String, Object> params, Object ret, String id, String methodSig, String filePath, Map<String, List<String>> fieldFilter) {
    write(self, params, ret, id, "exit", methodSig, filePath, fieldFilter);
  }

  private static final List<Map<String, Object>> records = new ArrayList<Map<String, Object>>();
  private static final Object lock = new Object();

  private static final int MAX_SERIALIZATION_DEPTH = 5;
  private static final String FRACTION_CLASS_NAME = "org.apache.commons.math.fraction.Fraction";
  private static final String SELF_ALIAS = "_self";
  private static final String RET_ALIAS = "_ret";

  private static synchronized void write(Object self, Map<String, Object> params, Object ret, String id, String phase, String methodSig, String filePath, Map<String, List<String>> fieldFilter) {
    try {
      Map<String, Set<String>> normalizedFilter = normalizeFieldFilter(fieldFilter);

      Map<String, Object> record = new LinkedHashMap<String, Object>();
      record.put("id", id);
      record.put("phase", phase);
      record.put("self", sanitizeRoot(self, SELF_ALIAS, normalizedFilter));
      record.put("params", sanitizeParams(params, normalizedFilter));
      record.put("ret", sanitizeRoot(ret, RET_ALIAS, normalizedFilter));
      record.put("method_signature", methodSig);
      record.put("file_path", filePath);

      synchronized (lock) {
        records.add(record);
      }

      String outPath = System.getenv("OBJDUMP_OUT");
      if (outPath == null || outPath.isEmpty()) {
        outPath = "objdump.out";
      }

      // Write all records as JSON array
      synchronized (lock) {
        FileWriter fw = null;
        BufferedWriter bw = null;
        try {
          fw = new FileWriter(outPath, false);
          bw = new BufferedWriter(fw);
          String json = toJson(records);
          bw.write(json);
          bw.flush();
        } finally {
          try { if (bw != null) bw.close(); } catch (IOException ignored) { }
          try { if (fw != null) fw.close(); } catch (IOException ignored) { }
        }
      }
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  private static Object sanitizeRoot(Object value, String alias, Map<String, Set<String>> fieldFilter) {
    return sanitizeForJson(value, alias, "", 0, new IdentityHashMap<Object, Boolean>(), fieldFilter);
  }

  private static Map<String, Object> sanitizeParams(Map<String, Object> params, Map<String, Set<String>> fieldFilter) {
    if (params == null) {
      return null;
    }
    Map<String, Object> sanitized = new LinkedHashMap<String, Object>();
    for (Map.Entry<String, Object> entry : params.entrySet()) {
      String key = entry.getKey();
      if (key == null) {
        key = "null";
      }
      sanitized.put(key, sanitizeForJson(entry.getValue(), key, "", 0, new IdentityHashMap<Object, Boolean>(), fieldFilter));
    }
    return sanitized;
  }

  private static Map<String, Set<String>> normalizeFieldFilter(Map<String, List<String>> fieldFilter) {
    if (fieldFilter == null || fieldFilter.isEmpty()) {
      return Collections.emptyMap();
    }
    Map<String, Set<String>> normalized = new LinkedHashMap<String, Set<String>>();
    for (Map.Entry<String, List<String>> entry : fieldFilter.entrySet()) {
      if (entry.getValue() == null) {
        continue;
      }
      LinkedHashSet<String> paths = new LinkedHashSet<String>();
      for (String rawPath : entry.getValue()) {
        if (rawPath == null) {
          continue;
        }
        String path = rawPath.trim();
        if (!path.isEmpty()) {
          paths.add(path);
        }
      }
      if (!paths.isEmpty()) {
        normalized.put(entry.getKey(), paths);
      }
    }
    return normalized.isEmpty() ? Collections.<String, Set<String>>emptyMap() : normalized;
  }

  private static Object sanitizeForJson(Object value, String alias, String currentPath, int depth, IdentityHashMap<Object, Boolean> visited, Map<String, Set<String>> fieldFilter) {
    if (value == null) {
      return null;
    }
    if (depth >= MAX_SERIALIZATION_DEPTH) {
      return "[MAX_DEPTH_REACHED]";
    }

    if (isPrimitiveLike(value)) {
      return normalizePrimitive(value);
    }

    if (visited.containsKey(value)) {
      return "[CYCLE_DETECTED]";
    }
    visited.put(value, Boolean.TRUE);

    Object sanitized;
    if (value instanceof Map<?, ?>) {
      sanitized = sanitizeMap((Map<?, ?>) value, alias, currentPath, depth, visited, fieldFilter);
    } else if (value instanceof Collection<?>) {
      sanitized = sanitizeCollection((Collection<?>) value, alias, currentPath, depth, visited, fieldFilter);
    } else if (value.getClass().isArray()) {
      sanitized = sanitizeArray(value, alias, currentPath, depth, visited, fieldFilter);
    } else if (FRACTION_CLASS_NAME.equals(value.getClass().getName())) {
      sanitized = sanitizeFraction(value, depth, visited);
    } else {
      sanitized = sanitizeObjectFields(value, alias, currentPath, depth, visited, fieldFilter);
    }

    visited.remove(value);
    return sanitized;
  }

  private static boolean isPrimitiveLike(Object value) {
    if (value instanceof Number && FRACTION_CLASS_NAME.equals(value.getClass().getName())) {
      return false;
    }
    return value instanceof String || value instanceof Number || value instanceof Boolean || value instanceof Character || value instanceof Enum<?>;
  }

  private static Object normalizePrimitive(Object value) {
    if (value instanceof Double) {
      Double d = (Double) value;
      if (Double.isNaN(d)) {
        return "NaN";
      }
      if (Double.isInfinite(d)) {
        return d > 0 ? "Infinity" : "-Infinity";
      }
      return d;
    }
    if (value instanceof Float) {
      Float f = (Float) value;
      if (Float.isNaN(f)) {
        return "NaN";
      }
      if (Float.isInfinite(f)) {
        return f > 0 ? "Infinity" : "-Infinity";
      }
      return f;
    }
    if (value instanceof Enum<?>) {
      return ((Enum<?>) value).name();
    }
    return value;
  }

  private static Map<String, Object> sanitizeFraction(Object fraction, int depth, IdentityHashMap<Object, Boolean> visited) {
    Map<String, Object> sanitized = new LinkedHashMap<String, Object>();
    sanitized.put("type", "Fraction");
    sanitized.put("numerator", invokeSafe(fraction, "getNumerator"));
    sanitized.put("denominator", invokeSafe(fraction, "getDenominator"));
    Object decimalValue = invokeSafe(fraction, "doubleValue");
    sanitized.put("doubleValue", normalizePrimitive(decimalValue));
    return sanitized;
  }

  private static Map<String, Object> sanitizeMap(Map<?, ?> map, String alias, String currentPath, int depth, IdentityHashMap<Object, Boolean> visited, Map<String, Set<String>> fieldFilter) {
    Map<String, Object> sanitized = new LinkedHashMap<String, Object>();
    for (Map.Entry<?, ?> entry : map.entrySet()) {
      String key = String.valueOf(entry.getKey());
      String nextPath = extendPath(currentPath, key);
      if (!shouldIncludeField(fieldFilter, alias, nextPath)) {
        continue;
      }
      sanitized.put(key, sanitizeForJson(entry.getValue(), alias, nextPath, depth + 1, visited, fieldFilter));
    }
    return sanitized;
  }

  private static List<Object> sanitizeCollection(Collection<?> collection, String alias, String currentPath, int depth, IdentityHashMap<Object, Boolean> visited, Map<String, Set<String>> fieldFilter) {
    List<Object> sanitized = new ArrayList<Object>(collection.size());
    for (Object item : collection) {
      sanitized.add(sanitizeForJson(item, alias, currentPath, depth + 1, visited, fieldFilter));
    }
    return sanitized;
  }

  private static List<Object> sanitizeArray(Object array, String alias, String currentPath, int depth, IdentityHashMap<Object, Boolean> visited, Map<String, Set<String>> fieldFilter) {
    int length = java.lang.reflect.Array.getLength(array);
    List<Object> sanitized = new ArrayList<Object>(length);
    for (int i = 0; i < length; i++) {
      Object item = java.lang.reflect.Array.get(array, i);
      sanitized.add(sanitizeForJson(item, alias, currentPath, depth + 1, visited, fieldFilter));
    }
    return sanitized;
  }

  private static Map<String, Object> sanitizeObjectFields(Object value, String alias, String currentPath, int depth, IdentityHashMap<Object, Boolean> visited, Map<String, Set<String>> fieldFilter) {
    Map<String, Object> sanitized = new LinkedHashMap<String, Object>();
    java.lang.reflect.Field[] fields = value.getClass().getDeclaredFields();
    for (java.lang.reflect.Field field : fields) {
      if (java.lang.reflect.Modifier.isStatic(field.getModifiers())) {
        continue;
      }
      String fieldName = field.getName();
      String nextPath = extendPath(currentPath, fieldName);
      if (!shouldIncludeField(fieldFilter, alias, nextPath)) {
        continue;
      }
      try {
        field.setAccessible(true);
        Object fieldValue = field.get(value);
        sanitized.put(fieldName, sanitizeForJson(fieldValue, alias, nextPath, depth + 1, visited, fieldFilter));
      } catch (Exception e) {
        sanitized.put(fieldName, "[SERIALIZATION_ERROR: " + e.getMessage() + "]");
      }
    }
    boolean hasAliasFilter = alias != null && fieldFilter.containsKey(alias);
    if (!hasAliasFilter || !sanitized.isEmpty()) {
      sanitized.put("_type", value.getClass().getName());
    }
    return sanitized;
  }

  private static boolean shouldIncludeField(Map<String, Set<String>> fieldFilter, String alias, String fieldPath) {
    if (fieldFilter.isEmpty() || alias == null) {
      return true;
    }
    Set<String> allowed = fieldFilter.get(alias);
    if (allowed == null || allowed.isEmpty()) {
      return true;
    }
    if (allowed.contains("*")) {
      return true;
    }
    if (fieldPath == null || fieldPath.isEmpty()) {
      return true;
    }
    for (String allowedPath : allowed) {
      if (allowedPath.equals(fieldPath) || allowedPath.startsWith(fieldPath + ".")) {
        return true;
      }
    }
    return false;
  }

  private static String extendPath(String currentPath, String segment) {
    if (segment == null || segment.isEmpty()) {
      return currentPath;
    }
    if (currentPath == null || currentPath.isEmpty()) {
      return segment;
    }
    return currentPath + "." + segment;
  }

  private static Object invokeSafe(Object target, String methodName) {
    try {
      java.lang.reflect.Method method = target.getClass().getMethod(methodName);
      method.setAccessible(true);
      return method.invoke(target);
    } catch (Exception e) {
      return "[SERIALIZATION_ERROR: " + e.getMessage() + "]";
    }
  }

  private static String toJson(Object value) {
    StringBuilder sb = new StringBuilder();
    appendJson(value, sb);
    return sb.toString();
  }

  private static void appendJson(Object value, StringBuilder sb) {
    if (value == null) {
      sb.append("null");
      return;
    }
    if (value instanceof String) {
      appendEscapedString((String) value, sb);
      return;
    }
    if (value instanceof Character) {
      appendEscapedString(String.valueOf(value), sb);
      return;
    }
    if (value instanceof Number) {
      sb.append(value.toString());
      return;
    }
    if (value instanceof Boolean) {
      sb.append(((Boolean) value) ? "true" : "false");
      return;
    }
    if (value instanceof Map<?, ?>) {
      sb.append('{');
      boolean first = true;
      for (Map.Entry<?, ?> entry : ((Map<?, ?>) value).entrySet()) {
        if (!first) {
          sb.append(',');
        }
        first = false;
        appendEscapedString(String.valueOf(entry.getKey()), sb);
        sb.append(':');
        appendJson(entry.getValue(), sb);
      }
      sb.append('}');
      return;
    }
    if (value instanceof Iterable<?>) {
      sb.append('[');
      boolean first = true;
      for (Object element : (Iterable<?>) value) {
        if (!first) {
          sb.append(',');
        }
        first = false;
        appendJson(element, sb);
      }
      sb.append(']');
      return;
    }
    if (value.getClass().isArray()) {
      sb.append('[');
      int length = java.lang.reflect.Array.getLength(value);
      for (int i = 0; i < length; i++) {
        if (i > 0) {
          sb.append(',');
        }
        appendJson(java.lang.reflect.Array.get(value, i), sb);
      }
      sb.append(']');
      return;
    }
    appendEscapedString(String.valueOf(value), sb);
  }

  private static void appendEscapedString(String value, StringBuilder sb) {
    sb.append('"');
    for (int i = 0; i < value.length(); i++) {
      char c = value.charAt(i);
      switch (c) {
        case '\\':
          sb.append("\\\\");
          break;
        case '"':
          sb.append("\\\"");
          break;
        case '\b':
          sb.append("\\b");
          break;
        case '\f':
          sb.append("\\f");
          break;
        case '\n':
          sb.append("\\n");
          break;
        case '\r':
          sb.append("\\r");
          break;
        case '\t':
          sb.append("\\t");
          break;
        default:
          if (c < 0x20) {
            sb.append(String.format("\\u%04x", (int) c));
          } else {
            sb.append(c);
          }
          break;
      }
    }
    sb.append('"');
  }
}