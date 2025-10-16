package org.objdump.instrumenter;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.util.List;
import java.util.Map;

/**
 * Formats instrumentation results as JSON
 */
public class OutputFormatter {
    
    private static final ObjectMapper mapper = new ObjectMapper();
    
    /**
     * Format instrumentation results as JSON matching Python output format
     */
    public static String formatResults(Map<String, List<CodeTransformer.TransformResult>> results) {
        ObjectNode root = mapper.createObjectNode();
        ObjectNode instrumented = mapper.createObjectNode();
        ArrayNode errors = mapper.createArrayNode();
        
        for (Map.Entry<String, List<CodeTransformer.TransformResult>> entry : results.entrySet()) {
            String filePath = entry.getKey();
            List<CodeTransformer.TransformResult> methodResults = entry.getValue();
            
            ArrayNode methodsArray = mapper.createArrayNode();
            for (CodeTransformer.TransformResult result : methodResults) {
                ObjectNode methodNode = mapper.createObjectNode();
                methodNode.put("signature", result.signature);
                methodNode.put("code", result.code);
                
                if (result.javadoc != null) {
                    ObjectNode javadocNode = mapper.createObjectNode();
                    javadocNode.put("description", result.javadoc.description);
                    
                    ObjectNode paramsNode = mapper.createObjectNode();
                    for (Map.Entry<String, String> param : result.javadoc.params.entrySet()) {
                        paramsNode.put(param.getKey(), param.getValue());
                    }
                    javadocNode.set("params", paramsNode);
                    
                    javadocNode.put("returns", result.javadoc.returns);
                    
                    ObjectNode throwsNode = mapper.createObjectNode();
                    for (Map.Entry<String, String> throwsEntry : result.javadoc.throwsInfo.entrySet()) {
                        throwsNode.put(throwsEntry.getKey(), throwsEntry.getValue());
                    }
                    javadocNode.set("throws", throwsNode);
                    
                    methodNode.set("javadoc", javadocNode);
                } else {
                    methodNode.putNull("javadoc");
                }
                
                methodsArray.add(methodNode);
            }
            
            instrumented.set(filePath, methodsArray);
        }
        
        root.set("instrumented", instrumented);
        root.set("errors", errors);
        
        try {
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(root);
        } catch (Exception e) {
            return "{\"instrumented\": {}, \"errors\": [\"" + e.getMessage() + "\"]}";
        }
    }
    
    /**
     * Format instrumentation results for a single file
     */
    public static String formatSingleFileResults(String filePath, List<CodeTransformer.TransformResult> results) {
        ArrayNode array = mapper.createArrayNode();
        
        for (CodeTransformer.TransformResult result : results) {
            ObjectNode node = mapper.createObjectNode();
            node.put("file", filePath);
            node.put("signature", result.signature);
            node.put("code", result.code);
            
            if (result.javadoc != null) {
                ObjectNode javadocNode = mapper.createObjectNode();
                javadocNode.put("description", result.javadoc.description);
                
                ObjectNode paramsNode = mapper.createObjectNode();
                for (Map.Entry<String, String> param : result.javadoc.params.entrySet()) {
                    paramsNode.put(param.getKey(), param.getValue());
                }
                javadocNode.set("params", paramsNode);
                
                javadocNode.put("returns", result.javadoc.returns);
                
                ObjectNode throwsNode = mapper.createObjectNode();
                for (Map.Entry<String, String> throwsEntry : result.javadoc.throwsInfo.entrySet()) {
                    throwsNode.put(throwsEntry.getKey(), throwsEntry.getValue());
                }
                javadocNode.set("throws", throwsNode);
                
                node.set("javadoc", javadocNode);
            } else {
                node.putNull("javadoc");
            }
            
            array.add(node);
        }
        
        try {
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(array);
        } catch (Exception e) {
            return "[]";
        }
    }
}

