package org.objdump.instrumenter;

import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.CallableDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.comments.JavadocComment;
import com.github.javaparser.javadoc.Javadoc;
import com.github.javaparser.javadoc.JavadocBlockTag;
import com.github.javaparser.javadoc.description.JavadocDescription;
import com.github.javaparser.javadoc.description.JavadocDescriptionElement;
import com.github.javaparser.javadoc.description.JavadocInlineTag;
import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;

import java.io.File;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import java.util.HashSet;

/**
 * Extracts and parses JavaDoc comments from methods
 */
public class JavaDocExtractor {
    
    /**
     * Structured JavaDoc information
     */
    public static class JavaDocInfo {
        public String description;
        public Map<String, String> params;
        public String returns;
        public Map<String, String> throwsInfo;
        public boolean hasInheritDoc;
        
        public JavaDocInfo() {
            this.params = new HashMap<>();
            this.throwsInfo = new HashMap<>();
            this.hasInheritDoc = false;
        }
    }
    
    /**
     * Extract JavaDoc from a method declaration
     */
    public static JavaDocInfo extractJavaDoc(MethodDeclaration method) {
        Optional<JavadocComment> javadocOpt = method.getJavadocComment();
        if (!javadocOpt.isPresent()) {
            return null;
        }
        
        return parseJavaDoc(javadocOpt.get().parse());
    }
    
    /**
     * Extract JavaDoc from a method declaration with inheritance resolution
     */
    public static JavaDocInfo extractJavaDoc(MethodDeclaration method, CompilationUnit cu, String currentFilePath) {
        Optional<JavadocComment> javadocOpt = method.getJavadocComment();
        if (!javadocOpt.isPresent()) {
            return null;
        }
        
        JavaDocInfo info = parseJavaDoc(javadocOpt.get().parse());
        
        // If @inheritDoc is found, resolve inheritance
        if (info != null && info.hasInheritDoc && cu != null && currentFilePath != null) {
            resolveInheritance(method, cu, currentFilePath, info);
        }
        
        return info;
    }
    
    /**
     * Extract JavaDoc from a constructor declaration
     */
    public static JavaDocInfo extractJavaDoc(ConstructorDeclaration constructor) {
        Optional<JavadocComment> javadocOpt = constructor.getJavadocComment();
        if (!javadocOpt.isPresent()) {
            return null;
        }
        
        return parseJavaDoc(javadocOpt.get().parse());
    }
    
    /**
     * Extract JavaDoc from a constructor declaration with inheritance resolution
     */
    public static JavaDocInfo extractJavaDoc(ConstructorDeclaration constructor, CompilationUnit cu, String currentFilePath) {
        Optional<JavadocComment> javadocOpt = constructor.getJavadocComment();
        if (!javadocOpt.isPresent()) {
            return null;
        }
        
        JavaDocInfo info = parseJavaDoc(javadocOpt.get().parse());
        
        // If @inheritDoc is found, resolve inheritance
        if (info != null && info.hasInheritDoc && cu != null && currentFilePath != null) {
            resolveInheritance(constructor, cu, currentFilePath, info);
        }
        
        return info;
    }
    
    /**
     * Process JavaDoc description elements and handle inline tags
     */
    private static String processJavaDocElements(JavadocDescription description, JavaDocInfo info) {
        if (description == null) {
            return "";
        }
        
        StringBuilder result = new StringBuilder();
        for (JavadocDescriptionElement element : description.getElements()) {
            if (element instanceof JavadocInlineTag) {
                JavadocInlineTag inlineTag = (JavadocInlineTag) element;
                String tagName = inlineTag.getName();
                
                // Handle @inheritDoc specifically
                if ("inheritDoc".equals(tagName)) {
                    info.hasInheritDoc = true;
                    result.append("{@inheritDoc}");
                } else {
                    // Preserve other inline tags
                    result.append("{@").append(tagName);
                    if (inlineTag.getContent() != null && !inlineTag.getContent().trim().isEmpty()) {
                        result.append(" ").append(inlineTag.getContent());
                    }
                    result.append("}");
                }
            } else {
                // Regular text element
                result.append(element.toText());
            }
        }
        
        return result.toString().trim();
    }
    
    /**
     * Check if description contains @inheritDoc and set flag accordingly
     */
    private static void checkForInheritDoc(String description, JavaDocInfo info) {
        if (description != null && description.contains("{@inheritDoc}")) {
            info.hasInheritDoc = true;
        }
    }
    
    /**
     * Parse JavaDoc into structured format
     */
    private static JavaDocInfo parseJavaDoc(Javadoc javadoc) {
        JavaDocInfo info = new JavaDocInfo();
        
        // Extract description
        JavadocDescription desc = javadoc.getDescription();
        if (desc != null) {
            info.description = processJavaDocElements(desc, info);
            // Check if description contains @inheritDoc
            checkForInheritDoc(info.description, info);
        }
        
        // Extract block tags (@param, @return, @throws, etc.)
        for (JavadocBlockTag tag : javadoc.getBlockTags()) {
            String tagName = tag.getTagName();
            String tagContent = processJavaDocElements(tag.getContent(), info);
            
            switch (tagName) {
                case "param":
                    // Extract parameter name and description
                    String paramName = tag.getName().isPresent() ? tag.getName().get() : "";
                    info.params.put(paramName, tagContent);
                    break;
                    
                case "return":
                case "returns":
                    info.returns = tagContent;
                    break;
                    
                case "throws":
                case "exception":
                    String exceptionType = tag.getName().isPresent() ? tag.getName().get() : "";
                    info.throwsInfo.put(exceptionType, tagContent);
                    break;
                    
                // Ignore other tags like @author, @since, @deprecated for now
            }
        }
        
        return info;
    }
    
    /**
     * Check if JavaDocInfo still contains @inheritDoc tags
     */
    private static boolean hasInheritDoc(JavaDocInfo info) {
        if (info == null) {
            return false;
        }
        
        // Check description
        if (info.description != null && info.description.contains("{@inheritDoc}")) {
            return true;
        }
        
        // Check if any @inheritDoc was found during parsing
        return info.hasInheritDoc;
    }
    
    /**
     * Generate unique identifier for method/constructor for cycle detection
     */
    private static String generateMethodSignature(CallableDeclaration<?> callable, String className) {
        StringBuilder signature = new StringBuilder();
        signature.append(className).append(".");
        
        if (callable instanceof MethodDeclaration) {
            MethodDeclaration method = (MethodDeclaration) callable;
            signature.append(method.getNameAsString());
        } else if (callable instanceof ConstructorDeclaration) {
            signature.append("<init>");
        }
        
        signature.append("(");
        for (int i = 0; i < callable.getParameters().size(); i++) {
            if (i > 0) signature.append(",");
            signature.append(callable.getParameters().get(i).getType().asString());
        }
        signature.append(")");
        
        return signature.toString();
    }
    
    /**
     * Resolve inheritance for JavaDoc with @inheritDoc tags
     */
    private static void resolveInheritance(CallableDeclaration<?> callable, CompilationUnit cu, String currentFilePath, JavaDocInfo info) {
        Set<String> visitedMethods = new HashSet<>();
        resolveInheritanceRecursive(callable, cu, currentFilePath, info, visitedMethods);
    }
    
    /**
     * Recursive helper for resolving inheritance with cycle detection
     */
    private static void resolveInheritanceRecursive(CallableDeclaration<?> callable, CompilationUnit cu, String currentFilePath, JavaDocInfo info, Set<String> visitedMethods) {
        try {
            // Generate unique signature for cycle detection
            String currentSignature = generateMethodSignature(callable, getCurrentClassName(cu));
            if (visitedMethods.contains(currentSignature)) {
                // Cycle detected, stop recursion
                return;
            }
            visitedMethods.add(currentSignature);
            
            // First try to find parent method in the same file
            JavaDocInfo parentInfo = findMatchingMethodInSameFile(callable, cu, visitedMethods);
            if (parentInfo != null) {
                mergeJavaDocInfo(info, parentInfo);
                
                // If parent also has @inheritDoc, continue resolving
                if (hasInheritDoc(parentInfo)) {
                    resolveInheritanceRecursive(callable, cu, currentFilePath, info, visitedMethods);
                }
                return;
            }
            
            // If not found in same file, look in parent class files
            List<String> parentPaths = findParentClassPaths(cu, currentFilePath);
            
            for (String parentPath : parentPaths) {
                JavaDocInfo parentInfoFromFile = findMatchingMethodJavaDoc(callable, parentPath, visitedMethods);
                if (parentInfoFromFile != null) {
                    mergeJavaDocInfo(info, parentInfoFromFile);
                    
                    // If parent also has @inheritDoc, continue resolving
                    if (hasInheritDoc(parentInfoFromFile)) {
                        resolveInheritanceRecursive(callable, cu, currentFilePath, info, visitedMethods);
                    }
                    break; // Use first match found
                }
            }
        } catch (Exception e) {
            // If inheritance resolution fails, keep original JavaDoc
            System.err.println("Warning: Could not resolve inheritance for " + callable.getName() + ": " + e.getMessage());
        }
    }
    
    /**
     * Get current class name from CompilationUnit
     */
    private static String getCurrentClassName(CompilationUnit cu) {
        Optional<ClassOrInterfaceDeclaration> classDecl = cu.findFirst(ClassOrInterfaceDeclaration.class);
        return classDecl.isPresent() ? classDecl.get().getNameAsString() : "Unknown";
    }
    
    /**
     * Find matching method JavaDoc in the same file (for inheritance within same file)
     */
    private static JavaDocInfo findMatchingMethodInSameFile(CallableDeclaration<?> callable, CompilationUnit cu) {
        return findMatchingMethodInSameFile(callable, cu, new HashSet<>());
    }
    
    /**
     * Find matching method JavaDoc in the same file with cycle detection
     */
    private static JavaDocInfo findMatchingMethodInSameFile(CallableDeclaration<?> callable, CompilationUnit cu, Set<String> visitedMethods) {
        // Find the class that contains this method
        ClassOrInterfaceDeclaration currentClass = null;
        for (ClassOrInterfaceDeclaration classDecl : cu.findAll(ClassOrInterfaceDeclaration.class)) {
            if (callable instanceof MethodDeclaration) {
                if (classDecl.findAll(MethodDeclaration.class).contains(callable)) {
                    currentClass = classDecl;
                    break;
                }
            } else if (callable instanceof ConstructorDeclaration) {
                if (classDecl.findAll(ConstructorDeclaration.class).contains(callable)) {
                    currentClass = classDecl;
                    break;
                }
            }
        }
        
        if (currentClass == null) {
            return null;
        }
        
        // Find parent class in the same file
        ClassOrInterfaceDeclaration parentClass = null;
        if (!currentClass.getExtendedTypes().isEmpty()) {
            String parentClassName = currentClass.getExtendedTypes().get(0).getNameAsString();
            for (ClassOrInterfaceDeclaration classDecl : cu.findAll(ClassOrInterfaceDeclaration.class)) {
                if (classDecl.getNameAsString().equals(parentClassName)) {
                    parentClass = classDecl;
                    break;
                }
            }
        }
        
        if (parentClass == null) {
            return null;
        }
        
        // Find matching method in parent class
        if (callable instanceof MethodDeclaration) {
            MethodDeclaration method = (MethodDeclaration) callable;
            for (MethodDeclaration parentMethod : parentClass.findAll(MethodDeclaration.class)) {
                if (isMatchingMethod(method, parentMethod)) {
                    JavaDocInfo parentInfo = extractJavaDoc(parentMethod);
                    
                    // If parent also has @inheritDoc, continue resolving recursively
                    if (parentInfo != null && hasInheritDoc(parentInfo)) {
                        // Create a new callable for the parent method and continue resolution
                        CallableDeclaration<?> parentCallable = parentMethod;
                        JavaDocInfo resolvedInfo = findMatchingMethodInSameFile(parentCallable, cu, visitedMethods);
                        if (resolvedInfo != null) {
                            // Merge the resolved info with the parent info
                            mergeJavaDocInfo(parentInfo, resolvedInfo);
                        }
                    }
                    
                    return parentInfo;
                }
            }
        } else if (callable instanceof ConstructorDeclaration) {
            ConstructorDeclaration constructor = (ConstructorDeclaration) callable;
            for (ConstructorDeclaration parentConstructor : parentClass.findAll(ConstructorDeclaration.class)) {
                if (isMatchingConstructor(constructor, parentConstructor)) {
                    JavaDocInfo parentInfo = extractJavaDoc(parentConstructor);
                    
                    // If parent also has @inheritDoc, continue resolving recursively
                    if (parentInfo != null && hasInheritDoc(parentInfo)) {
                        // Create a new callable for the parent constructor and continue resolution
                        CallableDeclaration<?> parentCallable = parentConstructor;
                        JavaDocInfo resolvedInfo = findMatchingMethodInSameFile(parentCallable, cu, visitedMethods);
                        if (resolvedInfo != null) {
                            // Merge the resolved info with the parent info
                            mergeJavaDocInfo(parentInfo, resolvedInfo);
                        }
                    }
                    
                    return parentInfo;
                }
            }
        }
        
        return null;
    }
    
    /**
     * Find parent class and interface file paths
     */
    private static List<String> findParentClassPaths(CompilationUnit cu, String currentFilePath) {
        List<String> parentPaths = new ArrayList<>();
        
        Optional<ClassOrInterfaceDeclaration> classDecl = cu.findFirst(ClassOrInterfaceDeclaration.class);
        if (!classDecl.isPresent()) {
            return parentPaths;
        }
        
        ClassOrInterfaceDeclaration classDeclaration = classDecl.get();
        
        // Find parent class
        if (!classDeclaration.getExtendedTypes().isEmpty()) {
            String parentPath = resolveParentClassPath(cu, currentFilePath, classDeclaration.getExtendedTypes().get(0));
            if (parentPath != null) {
                parentPaths.add(parentPath);
            }
        }
        
        // Find implemented interfaces
        for (ClassOrInterfaceType interfaceType : classDeclaration.getImplementedTypes()) {
            String interfacePath = resolveParentClassPath(cu, currentFilePath, interfaceType);
            if (interfacePath != null) {
                parentPaths.add(interfacePath);
            }
        }
        
        return parentPaths;
    }
    
    /**
     * Resolve parent class file path (adapted from TestMethodExtractor)
     */
    private static String resolveParentClassPath(CompilationUnit cu, String currentFilePath, ClassOrInterfaceType parentType) {
        String parentClassName = parentType.getNameAsString();
        
        // Check if parent class has a fully qualified name
        String parentPackageName = "";
        if (parentType.asString().contains(".")) {
            // Parent class has explicit package
            String fullParentName = parentType.asString();
            int lastDot = fullParentName.lastIndexOf('.');
            if (lastDot > 0) {
                parentPackageName = fullParentName.substring(0, lastDot);
                parentClassName = fullParentName.substring(lastDot + 1);
            }
        } else {
            // Parent class is imported or in the same package
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
     * Resolve package name from import statements
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
    
    /**
     * Find matching method JavaDoc in parent class
     */
    private static JavaDocInfo findMatchingMethodJavaDoc(CallableDeclaration<?> callable, String parentFilePath) {
        return findMatchingMethodJavaDoc(callable, parentFilePath, new HashSet<>());
    }
    
    /**
     * Find matching method JavaDoc in parent class with cycle detection
     */
    private static JavaDocInfo findMatchingMethodJavaDoc(CallableDeclaration<?> callable, String parentFilePath, Set<String> visitedMethods) {
        try {
            JavaParser parser = new JavaParser();
            ParseResult<CompilationUnit> parseResult = parser.parse(new File(parentFilePath));
            
            if (!parseResult.isSuccessful() || !parseResult.getResult().isPresent()) {
                return null;
            }
            
            CompilationUnit parentCu = parseResult.getResult().get();
            
            // Find matching method in parent class
            if (callable instanceof MethodDeclaration) {
                MethodDeclaration method = (MethodDeclaration) callable;
                for (MethodDeclaration parentMethod : parentCu.findAll(MethodDeclaration.class)) {
                    if (isMatchingMethod(method, parentMethod)) {
                        // Extract JavaDoc with inheritance resolution
                        JavaDocInfo parentInfo = extractJavaDoc(parentMethod, parentCu, parentFilePath);
                        return parentInfo;
                    }
                }
            } else if (callable instanceof ConstructorDeclaration) {
                ConstructorDeclaration constructor = (ConstructorDeclaration) callable;
                for (ConstructorDeclaration parentConstructor : parentCu.findAll(ConstructorDeclaration.class)) {
                    if (isMatchingConstructor(constructor, parentConstructor)) {
                        // Extract JavaDoc with inheritance resolution
                        JavaDocInfo parentInfo = extractJavaDoc(parentConstructor, parentCu, parentFilePath);
                        return parentInfo;
                    }
                }
            }
        } catch (Exception e) {
            // Parent file not found or cannot be parsed
        }
        
        return null;
    }
    
    /**
     * Check if two methods match (name and parameter types)
     */
    private static boolean isMatchingMethod(MethodDeclaration method1, MethodDeclaration method2) {
        if (!method1.getName().equals(method2.getName())) {
            return false;
        }
        
        if (method1.getParameters().size() != method2.getParameters().size()) {
            return false;
        }
        
        for (int i = 0; i < method1.getParameters().size(); i++) {
            String type1 = method1.getParameters().get(i).getType().asString();
            String type2 = method2.getParameters().get(i).getType().asString();
            
            // Simple type matching - could be enhanced for fully qualified names
            if (!type1.equals(type2) && !isCompatibleType(type1, type2)) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Check if two constructors match (parameter types)
     */
    private static boolean isMatchingConstructor(ConstructorDeclaration constructor1, ConstructorDeclaration constructor2) {
        if (constructor1.getParameters().size() != constructor2.getParameters().size()) {
            return false;
        }
        
        for (int i = 0; i < constructor1.getParameters().size(); i++) {
            String type1 = constructor1.getParameters().get(i).getType().asString();
            String type2 = constructor2.getParameters().get(i).getType().asString();
            
            if (!type1.equals(type2) && !isCompatibleType(type1, type2)) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Check if two types are compatible (simple name vs fully qualified)
     */
    private static boolean isCompatibleType(String type1, String type2) {
        // Extract simple name from fully qualified name
        String simple1 = type1.contains(".") ? type1.substring(type1.lastIndexOf('.') + 1) : type1;
        String simple2 = type2.contains(".") ? type2.substring(type2.lastIndexOf('.') + 1) : type2;
        
        return simple1.equals(simple2);
    }
    
    /**
     * Merge parent JavaDoc info into current info, replacing @inheritDoc
     */
    private static void mergeJavaDocInfo(JavaDocInfo current, JavaDocInfo parent) {
        // Replace description if it contains @inheritDoc
        if (current.description != null && current.description.contains("{@inheritDoc}")) {
            if (parent.description != null) {
                current.description = current.description.replaceAll("\\{@inheritDoc\\}", parent.description);
            } else {
                current.description = current.description.replaceAll("\\{@inheritDoc\\}", "");
            }
        }
        
        // Merge parameter documentation
        for (Map.Entry<String, String> parentParam : parent.params.entrySet()) {
            if (!current.params.containsKey(parentParam.getKey())) {
                current.params.put(parentParam.getKey(), parentParam.getValue());
            }
        }
        
        // Inherit return documentation if not present
        if ((current.returns == null || current.returns.trim().isEmpty()) && 
            parent.returns != null && !parent.returns.trim().isEmpty()) {
            current.returns = parent.returns;
        }
        
        // Merge throws documentation
        for (Map.Entry<String, String> parentThrow : parent.throwsInfo.entrySet()) {
            if (!current.throwsInfo.containsKey(parentThrow.getKey())) {
                current.throwsInfo.put(parentThrow.getKey(), parentThrow.getValue());
            }
        }
        
        // Update hasInheritDoc flag - check if current still has @inheritDoc after merging
        current.hasInheritDoc = current.description != null && current.description.contains("{@inheritDoc}");
    }
    
    /**
     * Extract method code (full source text)
     */
    public static String extractMethodCode(MethodDeclaration method) {
        return method.toString();
    }
    
    /**
     * Extract constructor code (full source text)
     */
    public static String extractMethodCode(ConstructorDeclaration constructor) {
        return constructor.toString();
    }
}

