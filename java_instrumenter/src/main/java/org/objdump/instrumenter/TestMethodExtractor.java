package org.objdump.instrumenter;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.AnnotationExpr;
import com.github.javaparser.ast.expr.Name;
import com.github.javaparser.ast.type.ClassOrInterfaceType;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

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
        Set<String> visitedClasses = new HashSet<>();
        return extractTestMethodsRecursive(javaFilePath, visitedClasses);
    }
    
    /**
     * Recursively extract test method names from a Java test class file and its parent classes.
     * 
     * @param javaFilePath Path to the Java test class file
     * @param visitedClasses Set to track visited classes and prevent infinite loops
     * @return List of test method names from current class and all parent classes
     * @throws IOException If file cannot be read or parsed
     */
    private static List<String> extractTestMethodsRecursive(String javaFilePath, Set<String> visitedClasses) throws IOException {
        JavaParser parser = new JavaParser();
        ParseResult<CompilationUnit> parseResult = parser.parse(new File(javaFilePath));
        
        if (!parseResult.isSuccessful() || !parseResult.getResult().isPresent()) {
            throw new IOException("Failed to parse Java file: " + javaFilePath);
        }
        
        CompilationUnit cu = parseResult.getResult().get();
        List<String> testMethods = new ArrayList<>();
        
        // Get the current class name to avoid infinite loops
        String currentClassName = getCurrentClassName(cu);
        if (currentClassName != null && visitedClasses.contains(currentClassName)) {
            return testMethods; // Already visited this class
        }
        if (currentClassName != null) {
            visitedClasses.add(currentClassName);
        }
        
        // Find all concrete test methods in the current class
        cu.findAll(MethodDeclaration.class).forEach(method -> {
            if (isTestMethod(method)) {
                testMethods.add(method.getName().asString());
            }
        });
        
        // Only recurse to parent if current class has NO test methods
        if (testMethods.isEmpty()) {
            // Find parent class and recursively extract test methods
            String parentClassPath = resolveParentClassPath(cu, javaFilePath);
            if (parentClassPath != null && new File(parentClassPath).exists()) {
                try {
                    List<String> parentTestMethods = extractTestMethodsRecursive(parentClassPath, visitedClasses);
                    testMethods.addAll(parentTestMethods);
                } catch (IOException e) {
                    // Parent class file not found or cannot be parsed, continue with current class only
                    System.err.println("Warning: Could not parse parent class " + parentClassPath + ": " + e.getMessage());
                }
            }
        }
        
        return testMethods;
    }
    
    /**
     * Check if a method is a test method.
     * Supports both JUnit 4 (@Test annotation) and JUnit 3 (public void test* methods).
     * Skips abstract methods as they won't be executed directly.
     */
    private static boolean isTestMethod(MethodDeclaration method) {
        // Skip abstract methods - they won't be executed directly
        if (method.isAbstract()) {
            return false;
        }
        
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
    
    /**
     * Get the current class name from the compilation unit.
     */
    private static String getCurrentClassName(CompilationUnit cu) {
        return cu.findFirst(ClassOrInterfaceDeclaration.class)
                .map(ClassOrInterfaceDeclaration::getNameAsString)
                .orElse(null);
    }
    
    /**
     * Resolve the parent class file path from the current class.
     * 
     * @param cu Current compilation unit
     * @param currentFilePath Path to the current class file
     * @return Path to the parent class file, or null if no parent or cannot resolve
     */
    private static String resolveParentClassPath(CompilationUnit cu, String currentFilePath) {
        // Find the class declaration
        Optional<ClassOrInterfaceDeclaration> classDecl = cu.findFirst(ClassOrInterfaceDeclaration.class);
        if (!classDecl.isPresent()) {
            return null;
        }
        
        ClassOrInterfaceDeclaration classDeclaration = classDecl.get();
        
        // Check if class extends another class
        if (classDeclaration.getExtendedTypes().isEmpty()) {
            return null; // No parent class
        }
        
        // Get the first extended type (parent class)
        ClassOrInterfaceType parentType = classDeclaration.getExtendedTypes().get(0);
        String parentClassName = parentType.getNameAsString();
        
        // Check if parent class has a fully qualified name (contains package)
        String parentPackageName = "";
        if (parentType.getScope().isPresent()) {
            // Parent class has explicit package (e.g., org.apache.commons.math.stat.descriptive.StorelessUnivariateStatisticAbstractTest)
            String fullParentName = parentType.asString();
            int lastDot = fullParentName.lastIndexOf('.');
            if (lastDot > 0) {
                parentPackageName = fullParentName.substring(0, lastDot);
                parentClassName = fullParentName.substring(lastDot + 1);
            }
        } else {
            // Parent class is imported or in the same package, need to resolve from imports
            parentPackageName = resolveParentPackageFromImports(cu, parentClassName);
            if (parentPackageName.isEmpty()) {
                // Fallback to same package as current class
                if (cu.getPackageDeclaration().isPresent()) {
                    parentPackageName = cu.getPackageDeclaration().get().getNameAsString();
                }
            }
        }
        
        // Convert package name to directory path
        String packagePath = parentPackageName.replace('.', '/');
        
        // Get the directory of the current file
        Path currentPath = Paths.get(currentFilePath);
        Path currentDir = currentPath.getParent();
        
        // Find the source root by looking for the package directory
        // Walk up the directory tree to find where the package structure starts
        Path searchDir = currentDir;
        while (searchDir != null) {
            Path packageDir = searchDir.resolve(packagePath);
            if (packageDir.toFile().exists()) {
                // Found the package directory, look for parent class here
                Path parentPath = packageDir.resolve(parentClassName + ".java");
                if (parentPath.toFile().exists()) {
                    return parentPath.toString();
                }
            }
            searchDir = searchDir.getParent();
        }
        
        // Fallback: try in the same directory as current file
        Path parentPath = currentDir.resolve(parentClassName + ".java");
        if (parentPath.toFile().exists()) {
            return parentPath.toString();
        }
        
        return null;
    }
    
    /**
     * Resolve the package name of a parent class from import statements.
     * 
     * @param cu Compilation unit
     * @param parentClassName Name of the parent class
     * @return Package name if found in imports, empty string otherwise
     */
    private static String resolveParentPackageFromImports(CompilationUnit cu, String parentClassName) {
        for (com.github.javaparser.ast.ImportDeclaration importDecl : cu.getImports()) {
            String importName = importDecl.getNameAsString();
            if (importName.endsWith("." + parentClassName)) {
                // Found the import for the parent class
                String packageName = importName.substring(0, importName.lastIndexOf('.'));
                return packageName;
            }
        }
        return "";
    }
}
