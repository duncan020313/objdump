package org.instrument;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.*;
import java.util.*;

public final class DebugDump {
  private static final ObjectMapper M = new ObjectMapper();
  private DebugDump() {}
  public static String newInvocationId() { return UUID.randomUUID().toString(); }
  public static void writeEntry(Object self, Map params, String id) { write(self, params, null, id, "entry"); }
  public static void writeExit(Object self, Map params, Object ret, String id) { write(self, params, ret, id, "exit"); }
  private static synchronized void write(Object self, Map params, Object ret, String id, String phase) {
    try {
      Map<String,Object> rec = new LinkedHashMap<>();
      rec.put("id", id);
      rec.put("phase", phase);
      rec.put("self", self);
      rec.put("params", params);
      rec.put("ret", ret);
      String json = M.writeValueAsString(rec);
      System.out.println("__INSTR__" + json);
    } catch (Exception ignored) { }
  }
}


