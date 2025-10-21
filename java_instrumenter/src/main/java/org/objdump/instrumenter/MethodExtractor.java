package org.objdump.instrumenter;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.CallableDeclaration;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.nodeTypes.NodeWithRange;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Extracts methods that intersect with changed line ranges
 */
public class MethodExtractor {
    
    /**
     * Information about a method that needs instrumentation
     */
    public static class MethodInfo {
        public String signature;
        public MethodDeclaration methodDeclaration;
        public ConstructorDeclaration constructorDeclaration;
        public boolean isConstructor;
        
        public MethodInfo(String signature, MethodDeclaration method) {
            this.signature = signature;
            this.methodDeclaration = method;
            this.isConstructor = false;
        }
        
        public MethodInfo(String signature, ConstructorDeclaration constructor) {
            this.signature = signature;
            this.constructorDeclaration = constructor;
            this.isConstructor = true;
        }
    }
    
    /**
     * Extract changed methods from a Java file based on diff ranges
     */
    public static List<MethodInfo> extractChangedMethods(String javaFilePath, List<DiffAnalyzer.Range> diffRanges) throws IOException {
        JavaParser parser = new JavaParser();
        ParseResult<CompilationUnit> parseResult = parser.parse(new File(javaFilePath));
        
        if (!parseResult.isSuccessful() || !parseResult.getResult().isPresent()) {
            throw new IOException("Failed to parse Java file: " + javaFilePath);
        }
        
        CompilationUnit cu = parseResult.getResult().get();
        
        // Convert diff ranges to a set of changed line numbers
        Set<Integer> changedLines = new HashSet<>();
        for (DiffAnalyzer.Range range : diffRanges) {
            for (int line = range.start; line <= range.end; line++) {
                changedLines.add(line);
            }
        }
        
        List<MethodInfo> methods = new ArrayList<>();
        
        // Find methods that intersect with changed lines
        cu.findAll(MethodDeclaration.class).forEach(method -> {
            if (method.getRange().isPresent() && intersectsChangedLines(method, changedLines)) {
                String signature = getMethodSignature(method);
                methods.add(new MethodInfo(signature, method));
            }
        });
        
        // Find constructors that intersect with changed lines
        cu.findAll(ConstructorDeclaration.class).forEach(constructor -> {
            if (constructor.getRange().isPresent() && intersectsChangedLines(constructor, changedLines)) {
                String signature = getConstructorSignature(constructor);
                methods.add(new MethodInfo(signature, constructor));
            }
        });
        
        return methods;
    }
    
    /**
     * Check if a node intersects with any changed line
     */
    private static boolean intersectsChangedLines(NodeWithRange<?> node, Set<Integer> changedLines) {
        if (!node.getRange().isPresent()) {
            return false;
        }
        
        int startLine = node.getRange().get().begin.line;
        int endLine = node.getRange().get().end.line;
        
        for (int line = startLine; line <= endLine; line++) {
            if (changedLines.contains(line)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Sanitize parameter name to allow only alphabetic characters
     */
    private static String sanitizeParamName(String paramName) {
        return paramName.replaceAll("[^a-zA-Z]", "");
    }
    
    /**
     * Normalize parameter type by removing 'final' modifier
     */
    private static String normalizeType(String typeString) {
        if (typeString == null) {
            return null;
        }
        // Remove leading 'final' keyword and any following whitespace
        return typeString.replaceFirst("^final\\s+", "").trim();
    }
    
    /**
     * Normalize signature by collapsing all whitespace (including newlines) to single spaces
     */
    private static String normalizeSignature(String signature) {
        if (signature == null) {
            return null;
        }
        // Replace multiple whitespace (including newlines) with single space and trim
        return signature.replaceAll("\\s+", " ").trim();
    }
    
    /**
     * Generate method signature (matching Python tree-sitter format)
     */
    private static String getMethodSignature(MethodDeclaration method) {
        StringBuilder sig = new StringBuilder();
        
        // Return type
        sig.append(method.getType().asString()).append(" ");
        
        // Method name
        sig.append(method.getName().asString());
        
        // Parameters
        sig.append("(");
        boolean first = true;
        for (Parameter param : method.getParameters()) {
            if (!first) {
                sig.append(", ");
            }
            sig.append(normalizeType(param.getType().asString()));
            if (param.isVarArgs()) {
                sig.append("...");
            }
            sig.append(" ").append(sanitizeParamName(param.getName().asString()));
            first = false;
        }
        sig.append(")");
        
        return sig.toString();
    }
    
    /**
     * Generate constructor signature (matching Python tree-sitter format)
     */
    private static String getConstructorSignature(ConstructorDeclaration constructor) {
        StringBuilder sig = new StringBuilder();
        
        // Constructor name
        sig.append(constructor.getName().asString());
        
        // Parameters
        sig.append("(");
        boolean first = true;
        for (Parameter param : constructor.getParameters()) {
            if (!first) {
                sig.append(", ");
            }
            sig.append(normalizeType(param.getType().asString()));
            if (param.isVarArgs()) {
                sig.append("...");
            }
            sig.append(" ").append(sanitizeParamName(param.getName().asString()));
            first = false;
        }
        sig.append(")");
        
        return sig.toString();
    }
    
    /**
     * Parse a Java file and find methods by signature
     */
    public static List<MethodInfo> findMethodsBySignature(String javaFilePath, List<String> targetSignatures) throws IOException {
        JavaParser parser = new JavaParser();
        ParseResult<CompilationUnit> parseResult = parser.parse(new File(javaFilePath));
        
        if (!parseResult.isSuccessful() || !parseResult.getResult().isPresent()) {
            throw new IOException("Failed to parse Java file: " + javaFilePath);
        }
        
        CompilationUnit cu = parseResult.getResult().get();
        // Normalize target signatures to handle whitespace differences
        Set<String> targetSet = new HashSet<>();
        for (String signature : targetSignatures) {
            targetSet.add(normalizeSignature(signature));
        }
        List<MethodInfo> methods = new ArrayList<>();
        
        // Find methods with matching signatures
        cu.findAll(MethodDeclaration.class).forEach(method -> {
            String signature = getMethodSignature(method);
            String normalizedSignature = normalizeSignature(signature);
            if (targetSet.contains(normalizedSignature)) {
                methods.add(new MethodInfo(signature, method));
            }
        });
        
        // Find constructors with matching signatures
        cu.findAll(ConstructorDeclaration.class).forEach(constructor -> {
            String signature = getConstructorSignature(constructor);
            String normalizedSignature = normalizeSignature(signature);
            if (targetSet.contains(normalizedSignature)) {
                methods.add(new MethodInfo(signature, constructor));
            }
        });
        
        return methods;
    }
}

