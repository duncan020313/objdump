package org.objdump.instrumenter;

import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.CallableDeclaration;
import com.github.javaparser.ast.comments.JavadocComment;
import com.github.javaparser.javadoc.Javadoc;
import com.github.javaparser.javadoc.JavadocBlockTag;
import com.github.javaparser.javadoc.description.JavadocDescription;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

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
        
        public JavaDocInfo() {
            this.params = new HashMap<>();
            this.throwsInfo = new HashMap<>();
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
     * Parse JavaDoc into structured format
     */
    private static JavaDocInfo parseJavaDoc(Javadoc javadoc) {
        JavaDocInfo info = new JavaDocInfo();
        
        // Extract description
        JavadocDescription desc = javadoc.getDescription();
        if (desc != null) {
            info.description = desc.toText().trim();
        }
        
        // Extract block tags (@param, @return, @throws, etc.)
        for (JavadocBlockTag tag : javadoc.getBlockTags()) {
            String tagName = tag.getTagName();
            String tagContent = tag.getContent().toText().trim();
            
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

