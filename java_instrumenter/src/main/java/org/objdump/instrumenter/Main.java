package org.objdump.instrumenter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.*;
import java.util.*;

/**
 * CLI entry point for Java instrumenter
 */
public class Main {
    
    private static final ObjectMapper mapper = new ObjectMapper();
    
    public static void main(String[] args) {
        try {
            if (args.length == 0) {
                printUsage();
                System.exit(1);
            }
            
            String command = args[0];
            
            switch (command) {
                case "instrument":
                    handleInstrument(args);
                    break;
                    
                case "diff":
                    handleDiff(args);
                    break;
                    
                case "extract-methods":
                    handleExtractMethods(args);
                    break;
                    
                default:
                    System.err.println("Unknown command: " + command);
                    printUsage();
                    System.exit(1);
            }
            
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }
    
    /**
     * Handle instrument command
     * Usage: instrument <java_file> <signature1> [<signature2> ...]
     */
    private static void handleInstrument(String[] args) throws IOException {
        if (args.length < 3) {
            System.err.println("Usage: instrument <java_file> <signature1> [<signature2> ...]");
            System.exit(1);
        }
        
        String javaFile = args[1];
        List<String> signatures = new ArrayList<>();
        for (int i = 2; i < args.length; i++) {
            signatures.add(args[i]);
        }
        
        List<CodeTransformer.TransformResult> results = CodeTransformer.instrumentJavaFile(javaFile, signatures);
        String output = OutputFormatter.formatSingleFileResults(javaFile, results);
        System.out.println(output);
    }
    
    /**
     * Handle diff command
     * Usage: diff <buggy_file> <fixed_file>
     */
    private static void handleDiff(String[] args) throws IOException {
        if (args.length < 3) {
            System.err.println("Usage: diff <buggy_file> <fixed_file>");
            System.exit(1);
        }
        
        String buggyFile = args[1];
        String fixedFile = args[2];
        
        DiffAnalyzer.DiffResult result = DiffAnalyzer.computeDiff(buggyFile, fixedFile);
        
        // Output as JSON
        Map<String, Object> output = new HashMap<>();
        
        List<Map<String, Integer>> leftRanges = new ArrayList<>();
        for (DiffAnalyzer.Range range : result.leftRanges) {
            Map<String, Integer> r = new HashMap<>();
            r.put("start", range.start);
            r.put("end", range.end);
            leftRanges.add(r);
        }
        
        List<Map<String, Integer>> rightRanges = new ArrayList<>();
        for (DiffAnalyzer.Range range : result.rightRanges) {
            Map<String, Integer> r = new HashMap<>();
            r.put("start", range.start);
            r.put("end", range.end);
            rightRanges.add(r);
        }
        
        output.put("left", leftRanges);
        output.put("right", rightRanges);
        
        System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(output));
    }
    
    /**
     * Handle extract-methods command
     * Usage: extract-methods <java_file> <start1:end1> [<start2:end2> ...]
     */
    private static void handleExtractMethods(String[] args) throws IOException {
        if (args.length < 3) {
            System.err.println("Usage: extract-methods <java_file> <start1:end1> [<start2:end2> ...]");
            System.exit(1);
        }
        
        String javaFile = args[1];
        List<DiffAnalyzer.Range> ranges = new ArrayList<>();
        
        for (int i = 2; i < args.length; i++) {
            String[] parts = args[i].split(":");
            if (parts.length == 2) {
                int start = Integer.parseInt(parts[0]);
                int end = Integer.parseInt(parts[1]);
                ranges.add(new DiffAnalyzer.Range(start, end));
            }
        }
        
        List<MethodExtractor.MethodInfo> methods = MethodExtractor.extractChangedMethods(javaFile, ranges);
        
        // Output signatures as JSON array
        List<String> signatures = new ArrayList<>();
        for (MethodExtractor.MethodInfo method : methods) {
            signatures.add(method.signature);
        }
        
        System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(signatures));
    }
    
    /**
     * Print usage information
     */
    private static void printUsage() {
        System.err.println("Java Instrumenter CLI");
        System.err.println();
        System.err.println("Commands:");
        System.err.println("  instrument <java_file> <signature1> [<signature2> ...]");
        System.err.println("      Instrument the specified methods in a Java file");
        System.err.println();
        System.err.println("  diff <buggy_file> <fixed_file>");
        System.err.println("      Compute diff and extract changed line ranges");
        System.err.println();
        System.err.println("  extract-methods <java_file> <start1:end1> [<start2:end2> ...]");
        System.err.println("      Extract method signatures that intersect with given line ranges");
        System.err.println();
    }
}

