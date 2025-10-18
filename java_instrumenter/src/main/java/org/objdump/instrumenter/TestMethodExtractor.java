package org.objdump.instrumenter;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.AnnotationExpr;
import com.github.javaparser.ast.expr.Name;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Extracts test methods from Java test class files.
 * Supports both JUnit 4 (@Test annotation) and JUnit 3 (public void test* methods).
 */
public class TestMethodExtractor {
    
    /**
     * Extract test method names from a Java test class file.
     * 
     * @param javaFilePath Path to the Java test class file
     * @return List of test method names
     * @throws IOException If file cannot be read or parsed
     */
    public static List<String> extractTestMethods(String javaFilePath) throws IOException {
        JavaParser parser = new JavaParser();
        ParseResult<CompilationUnit> parseResult = parser.parse(new File(javaFilePath));
        
        if (!parseResult.isSuccessful() || !parseResult.getResult().isPresent()) {
            throw new IOException("Failed to parse Java file: " + javaFilePath);
        }
        
        CompilationUnit cu = parseResult.getResult().get();
        List<String> testMethods = new ArrayList<>();
        
        // Find all methods in the class
        cu.findAll(MethodDeclaration.class).forEach(method -> {
            if (isTestMethod(method)) {
                testMethods.add(method.getName().asString());
            }
        });
        
        return testMethods;
    }
    
    /**
     * Check if a method is a test method.
     * Supports both JUnit 4 (@Test annotation) and JUnit 3 (public void test* methods).
     */
    private static boolean isTestMethod(MethodDeclaration method) {
        // Check for JUnit 4 @Test annotation
        if (method.getAnnotations() != null) {
            for (AnnotationExpr annotation : method.getAnnotations()) {
                if (annotation.getName() instanceof Name) {
                    Name name = (Name) annotation.getName();
                    if ("Test".equals(name.asString())) {
                        return true;
                    }
                }
            }
        }
        
        // Check for JUnit 3 style test methods (public void test*)
        if (method.isPublic() && 
            method.getType().isVoidType() && 
            method.getName().asString().startsWith("test")) {
            return true;
        }
        
        return false;
    }
}
