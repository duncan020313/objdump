package org.instrument;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public final class DebugDump {
  private static final ObjectMapper M = new ObjectMapper();
  // Store entry payloads by invocation id until exit is called
  private static final Map<String, Map<String, Object>> ENTRIES = new ConcurrentHashMap<String, Map<String, Object>>();

  private DebugDump() {}

  public static String newInvocationId() { return UUID.randomUUID().toString(); }

  public static synchronized void writeEntry(Object self, Map params, String id) {
    try {
      Map<String, Object> entry = new LinkedHashMap<String, Object>();
      entry.put("self", self);
      entry.put("params", params);
      ENTRIES.put(id, entry);
    } catch (Exception ignored) { }
  }

  public static synchronized void writeExit(Object self, Map params, Object ret, String id) {
    try {
      Map<String, Object> entry = ENTRIES.remove(id);
      if (entry == null) {
        entry = new LinkedHashMap<String, Object>();
        entry.put("self", self);
        entry.put("params", params);
      }
      Map<String, Object> exit = new LinkedHashMap<String, Object>();
      exit.put("self", self);
      exit.put("ret", ret);

      Map<String, Object> combined = new LinkedHashMap<String, Object>();
      combined.put("id", id);
      combined.put("entry", entry);
      combined.put("exit", exit);

      String json = M.writeValueAsString(combined);

      String outPath = System.getenv("OBJDUMP_OUT");
      if (outPath == null || outPath.isEmpty()) {
        System.out.println(json);
      } else {
        try (FileWriter fw = new FileWriter(outPath, true); BufferedWriter bw = new BufferedWriter(fw)) {
          bw.write(json);
          bw.newLine();
          bw.flush();
        }
      }
    } catch (Exception ignored) { }
  }
}


