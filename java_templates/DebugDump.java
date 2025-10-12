package org.instrument;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.introspect.JacksonAnnotationIntrospector;
import com.fasterxml.jackson.databind.introspect.AnnotatedMethod;
import com.fasterxml.jackson.databind.introspect.VisibilityChecker;
import java.io.*;
import java.util.*;

public final class DebugDump {
    private static final ObjectMapper M = new ObjectMapper()
    .disable(MapperFeature.USE_ANNOTATIONS)
    .disable(SerializationFeature.FAIL_ON_EMPTY_BEANS)
    .setVisibility(VisibilityChecker.Std.defaultInstance()
      .withGetterVisibility(com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.NONE)
      .withFieldVisibility(com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.ANY));


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
    } catch (Exception ignored) { }
  }
}