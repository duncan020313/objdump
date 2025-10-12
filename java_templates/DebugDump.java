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
import java.io.*;
import java.util.*;

public final class DebugDump {
    // Custom serializer that limits depth to 3
    private static class DepthLimitedSerializer extends JsonSerializer<Object> {
        private static final int MAX_DEPTH = 10;
        
        @Override
        public void serialize(Object value, JsonGenerator gen, SerializerProvider serializers) throws IOException {
            serializeWithDepth(value, gen, serializers, 0);
        }
        
        private void serializeWithDepth(Object value, JsonGenerator gen, SerializerProvider serializers, int currentDepth) throws IOException {
            if (currentDepth >= MAX_DEPTH) {
                gen.writeString("[MAX_DEPTH_REACHED]");
                return;
            }
            
            if (value == null) {
                gen.writeNull();
            } else if (value instanceof String) {
                gen.writeString((String) value);
            } else if (value instanceof Number) {
                gen.writeNumber(value.toString());
            } else if (value instanceof Boolean) {
                gen.writeBoolean((Boolean) value);
            } else if (value instanceof Map) {
                gen.writeStartObject();
                for (Map.Entry<?, ?> entry : ((Map<?, ?>) value).entrySet()) {
                    gen.writeFieldName(entry.getKey().toString());
                    serializeWithDepth(entry.getValue(), gen, serializers, currentDepth + 1);
                }
                gen.writeEndObject();
            } else if (value instanceof Collection) {
                gen.writeStartArray();
                for (Object item : (Collection<?>) value) {
                    serializeWithDepth(item, gen, serializers, currentDepth + 1);
                }
                gen.writeEndArray();
            } else if (value.getClass().isArray()) {
                gen.writeStartArray();
                Object[] array = (Object[]) value;
                for (Object item : array) {
                    serializeWithDepth(item, gen, serializers, currentDepth + 1);
                }
                gen.writeEndArray();
            } else {
                // For other objects, try to serialize their fields
                gen.writeStartObject();
                try {
                    java.lang.reflect.Field[] fields = value.getClass().getDeclaredFields();
                    for (java.lang.reflect.Field field : fields) {
                        field.setAccessible(true);
                        Object fieldValue = field.get(value);
                        gen.writeFieldName(field.getName());
                        serializeWithDepth(fieldValue, gen, serializers, currentDepth + 1);
                    }
                } catch (Exception e) {
                    gen.writeString("[SERIALIZATION_ERROR: " + e.getMessage() + "]");
                }
                gen.writeEndObject();
            }
        }
    }
    
    private static final ObjectMapper M = new ObjectMapper()
    .disable(MapperFeature.USE_ANNOTATIONS)
    .disable(SerializationFeature.FAIL_ON_EMPTY_BEANS)
    .setVisibility(VisibilityChecker.Std.defaultInstance()
      .withGetterVisibility(com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.NONE)
      .withFieldVisibility(com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.ANY));
    
    static {
        // Register the depth-limited serializer
        SimpleModule module = new SimpleModule();
        module.addSerializer(Object.class, new DepthLimitedSerializer());
        M.registerModule(module);
    }


  private DebugDump() {}

  public static String newInvocationId() { 
    return UUID.randomUUID().toString(); 
  }

  public static void writeEntry(Object self, Map<String, Object> params, String id) {
    write(self, params, null, id, "entry");
  }

  public static void writeExit(Object self, Map<String, Object> params, Object ret, String id) {
    write(self, params, ret, id, "exit");
  }

  private static synchronized void write(Object self, Map<String, Object> params, Object ret, String id, String phase) {
    try {
      Map<String, Object> record = new LinkedHashMap<String, Object>();
      record.put("id", id);
      record.put("phase", phase);
      record.put("self", self);
      record.put("params", params);
      record.put("ret", ret);

      String json = M.writeValueAsString(record);

      String outPath = System.getenv("OBJDUMP_OUT");
      if (outPath == null || outPath.isEmpty()) {
        outPath = "objdump.out";
      }
      
      FileWriter fw = null;
      BufferedWriter bw = null;
      try {
        fw = new FileWriter(outPath, true);
        bw = new BufferedWriter(fw);
        bw.write(json);
        bw.newLine();
        bw.flush();
      } finally {
        try { if (bw != null) bw.close(); } catch (IOException ignored) { }
        try { if (fw != null) fw.close(); } catch (IOException ignored) { }
      }
    } catch (Exception e) { 
        throw new RuntimeException(e);
    }
  }
}