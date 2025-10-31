package org.instrument;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.introspect.JacksonAnnotationIntrospector;
import com.fasterxml.jackson.databind.introspect.AnnotatedMethod;
import com.fasterxml.jackson.databind.introspect.VisibilityChecker;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.databind.BeanDescription;
import com.fasterxml.jackson.databind.SerializationConfig;
import com.fasterxml.jackson.databind.ser.BeanSerializerModifier;
import java.io.*;
import java.util.*;

public final class DebugDump {
    // Custom serializer that limits depth to 3
    private static class DepthLimitedSerializer extends JsonSerializer<Object> {
        private static final int MAX_DEPTH = 5;

        @Override
        public void serialize(Object value, JsonGenerator gen, SerializerProvider serializers) throws IOException {
            serializeWithDepth(value, gen, serializers, 0, new IdentityHashMap<Object, Boolean>());
        }

      private void serializeWithDepth(Object value, JsonGenerator gen, SerializerProvider serializers, int currentDepth, IdentityHashMap<Object, Boolean> visited) throws IOException {
            if (currentDepth >= MAX_DEPTH) {
                gen.writeString("[MAX_DEPTH_REACHED]");
                return;
            }

            if (value == null) {
                gen.writeNull();
                return;
            }

            if (visited.containsKey(value)) {
                gen.writeString("[CYCLE_DETECTED]");
                return;
            }
            visited.put(value, Boolean.TRUE);

            try {
                if (value instanceof String) {
                    gen.writeString((String) value);
                } else if (value instanceof Number) {
                    // Preserve special floating values as strings
                    if (value instanceof Double) {
                        Double d = (Double) value;
                        if (Double.isNaN(d)) {
                            gen.writeString("NaN");
                        } else if (Double.isInfinite(d)) {
                            gen.writeString(d > 0 ? "Infinity" : "-Infinity");
                        } else {
                            gen.writeNumber(value.toString());
                        }
                    } else if (value instanceof Float) {
                        Float f = (Float) value;
                        if (Float.isNaN(f)) {
                            gen.writeString("NaN");
                        } else if (Float.isInfinite(f)) {
                            gen.writeString(f > 0 ? "Infinity" : "-Infinity");
                        } else {
                            gen.writeNumber(value.toString());
                        }
                    } else {
                        gen.writeNumber(value.toString());
                    }
                } else if (value instanceof Boolean) {
                    gen.writeBoolean((Boolean) value);
                } else if (value instanceof Map) {
                    gen.writeStartObject();
                    for (Map.Entry<?, ?> entry : ((Map<?, ?>) value).entrySet()) {
                        String key = String.valueOf(entry.getKey());
                        gen.writeFieldName(key);
                        serializeWithDepth(entry.getValue(), gen, serializers, currentDepth + 1, visited);
                    }
                    gen.writeEndObject();
                } else if (value instanceof Collection) {
                    gen.writeStartArray();
                    for (Object item : (Collection<?>) value) {
                        serializeWithDepth(item, gen, serializers, currentDepth + 1, visited);
                    }
                    gen.writeEndArray();
                } else if (value.getClass().isArray()) {
                    gen.writeStartArray();
                    int length = java.lang.reflect.Array.getLength(value);
                    for (int i = 0; i < length; i++) {
                        Object item = java.lang.reflect.Array.get(value, i);
                        serializeWithDepth(item, gen, serializers, currentDepth + 1, visited);
                    }
                    gen.writeEndArray();
                } else {
                    // For other objects, try to serialize their non-static, non-synthetic fields
                    gen.writeStartObject();
                    try {
                        java.lang.reflect.Field[] fields = value.getClass().getDeclaredFields();
                        for (java.lang.reflect.Field field : fields) {
                            if (java.lang.reflect.Modifier.isStatic(field.getModifiers()) || field.isSynthetic()) {
                                continue;
                            }
                            field.setAccessible(true);
                            Object fieldValue = field.get(value);
                            gen.writeFieldName(field.getName());
                            serializeWithDepth(fieldValue, gen, serializers, currentDepth + 1, visited);
                        }
                    } catch (Exception e) {
                        gen.writeFieldName("_error");
                        gen.writeString("[SERIALIZATION_ERROR: " + e.getMessage() + "]");
                    }
                    gen.writeEndObject();
                }
            } finally {
                visited.remove(value);
            }
        }
    }

    private static final ObjectMapper M = createObjectMapper();

    private static ObjectMapper createObjectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.disable(MapperFeature.USE_ANNOTATIONS);
        mapper.disable(SerializationFeature.FAIL_ON_EMPTY_BEANS);

        // Configure visibility to access all fields
        mapper.setVisibility(mapper.getSerializationConfig()
            .getDefaultVisibilityChecker()
            .withFieldVisibility(com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.ANY)
            .withGetterVisibility(com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.NONE)
            .withSetterVisibility(com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.NONE)
            .withCreatorVisibility(com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.NONE));

        // Register the depth-limited serializer for all objects
        SimpleModule module = new SimpleModule();
        module.setSerializerModifier(new BeanSerializerModifier() {
            @Override
            public JsonSerializer<?> modifySerializer(SerializationConfig config, BeanDescription beanDesc, JsonSerializer<?> serializer) {
                return new DepthLimitedSerializer();
            }
        });
        mapper.registerModule(module);

        return mapper;
    }


  private DebugDump() {}

  public static String newInvocationId() {
    return UUID.randomUUID().toString();
  }

  public static void writeEntry(Object self, Map<String, Object> params, String id, String methodSig, String filePath) {
    write(self, params, null, id, "entry", methodSig, filePath);
  }

  public static void writeExit(Object self, Map<String, Object> params, Object ret, String id, String methodSig, String filePath) {
    write(self, params, ret, id, "exit", methodSig, filePath);
  }

  private static final List<Map<String, Object>> records = new ArrayList<Map<String, Object>>();
  private static final Object lock = new Object();

    private static final int MAX_SERIALIZATION_DEPTH = 5;
    private static final String FRACTION_CLASS_NAME = "org.apache.commons.math.fraction.Fraction";

    private static synchronized void write(Object self, Map<String, Object> params, Object ret, String id, String phase, String methodSig, String filePath) {
    try {
      Map<String, Object> record = new LinkedHashMap<String, Object>();
      record.put("id", id);
      record.put("phase", phase);
      record.put("self", sanitizeForJson(self));
      record.put("params", sanitizeForJson(params));
      record.put("ret", sanitizeForJson(ret));
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
          String json = M.writeValueAsString(records);
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

  private static Object sanitizeForJson(Object value) {
    return sanitizeForJson(value, 0, new IdentityHashMap<Object, Boolean>());
  }

  private static Object sanitizeForJson(Object value, int depth, IdentityHashMap<Object, Boolean> visited) {
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
      sanitized = sanitizeMap((Map<?, ?>) value, depth, visited);
    } else if (value instanceof Collection<?>) {
      sanitized = sanitizeCollection((Collection<?>) value, depth, visited);
    } else if (value.getClass().isArray()) {
      sanitized = sanitizeArray(value, depth, visited);
    } else if (FRACTION_CLASS_NAME.equals(value.getClass().getName())) {
      sanitized = sanitizeFraction(value, depth, visited);
    } else {
      sanitized = sanitizeObjectFields(value, depth, visited);
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

  private static Map<String, Object> sanitizeMap(Map<?, ?> map, int depth, IdentityHashMap<Object, Boolean> visited) {
    Map<String, Object> sanitized = new LinkedHashMap<String, Object>();
    for (Map.Entry<?, ?> entry : map.entrySet()) {
      String key = String.valueOf(entry.getKey());
      sanitized.put(key, sanitizeForJson(entry.getValue(), depth + 1, visited));
    }
    return sanitized;
  }

  private static List<Object> sanitizeCollection(Collection<?> collection, int depth, IdentityHashMap<Object, Boolean> visited) {
    List<Object> sanitized = new ArrayList<Object>(collection.size());
    for (Object item : collection) {
      sanitized.add(sanitizeForJson(item, depth + 1, visited));
    }
    return sanitized;
  }

  private static List<Object> sanitizeArray(Object array, int depth, IdentityHashMap<Object, Boolean> visited) {
    int length = java.lang.reflect.Array.getLength(array);
    List<Object> sanitized = new ArrayList<Object>(length);
    for (int i = 0; i < length; i++) {
      Object item = java.lang.reflect.Array.get(array, i);
      sanitized.add(sanitizeForJson(item, depth + 1, visited));
    }
    return sanitized;
  }

  private static Map<String, Object> sanitizeObjectFields(Object value, int depth, IdentityHashMap<Object, Boolean> visited) {
    Map<String, Object> sanitized = new LinkedHashMap<String, Object>();
    java.lang.reflect.Field[] fields = value.getClass().getDeclaredFields();
    for (java.lang.reflect.Field field : fields) {
      if (java.lang.reflect.Modifier.isStatic(field.getModifiers())) {
        continue;
      }
      try {
        field.setAccessible(true);
        Object fieldValue = field.get(value);
        sanitized.put(field.getName(), sanitizeForJson(fieldValue, depth + 1, visited));
      } catch (Exception e) {
        sanitized.put(field.getName(), "[SERIALIZATION_ERROR: " + e.getMessage() + "]");
      }
    }
    sanitized.put("_type", value.getClass().getName());
    return sanitized;
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
}