package org.objdump.instrumenter;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Analyzes unified diff output to extract changed line ranges
 */
public class DiffAnalyzer {
    
    private static final Pattern HUNK_HEADER = Pattern.compile("@@ -(\\d+)(?:,(\\d+))? \\+(\\d+)(?:,(\\d+))? @@");
    
    /**
     * Range representing start and end line numbers
     */
    public static class Range {
        public final int start;
        public final int end;
        
        public Range(int start, int end) {
            this.start = start;
            this.end = end;
        }
    }
    
    /**
     * Result of diff analysis containing left (buggy) and right (fixed) ranges
     */
    public static class DiffResult {
        public final List<Range> leftRanges;
        public final List<Range> rightRanges;
        
        public DiffResult(List<Range> leftRanges, List<Range> rightRanges) {
            this.leftRanges = leftRanges;
            this.rightRanges = rightRanges;
        }
    }
    
    /**
     * Compute diff between two files and extract changed line ranges
     */
    public static DiffResult computeDiff(String buggyFile, String fixedFile) throws IOException {
        ProcessBuilder pb = new ProcessBuilder("diff", "-U", "0", buggyFile, fixedFile);
        Process process = pb.start();
        
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
        }
        
        try {
            int exitCode = process.waitFor();
            // Exit code 0 means no differences, 1 means differences found
            if (exitCode == 0) {
                return new DiffResult(new ArrayList<>(), new ArrayList<>());
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("Diff process interrupted", e);
        }
        
        return parseDiff(output.toString());
    }
    
    /**
     * Parse unified diff format and extract line ranges
     */
    public static DiffResult parseDiff(String diffText) {
        List<Range> leftRanges = new ArrayList<>();
        List<Range> rightRanges = new ArrayList<>();
        
        String[] lines = diffText.split("\n");
        for (String line : lines) {
            if (line.startsWith("@@ ")) {
                Matcher matcher = HUNK_HEADER.matcher(line);
                if (matcher.find()) {
                    try {
                        int leftStart = Integer.parseInt(matcher.group(1));
                        String leftCountStr = matcher.group(2);
                        int leftCount = leftCountStr != null ? Integer.parseInt(leftCountStr) : 1;
                        
                        int rightStart = Integer.parseInt(matcher.group(3));
                        String rightCountStr = matcher.group(4);
                        int rightCount = rightCountStr != null ? Integer.parseInt(rightCountStr) : 1;
                        
                        if (leftCount > 0) {
                            int leftEnd = leftStart + leftCount - 1;
                            leftRanges.add(new Range(leftStart, Math.max(leftEnd, leftStart)));
                        }
                        
                        if (rightCount > 0) {
                            int rightEnd = rightStart + rightCount - 1;
                            rightRanges.add(new Range(rightStart, Math.max(rightEnd, rightStart)));
                        }
                    } catch (NumberFormatException e) {
                        // Skip malformed hunk headers
                    }
                }
            }
        }
        
        return new DiffResult(leftRanges, rightRanges);
    }
}

