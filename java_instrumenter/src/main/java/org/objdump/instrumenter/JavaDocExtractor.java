package org.objdump.instrumenter;

import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.CallableDeclaration;
import com.github.javaparser.ast.comments.JavadocComment;
import com.github.javaparser.javadoc.Javadoc;
import com.github.javaparser.javadoc.JavadocBlockTag;
import com.github.javaparser.javadoc.description.JavadocDescription;
import com.github.javaparser.javadoc.description.JavadocDescriptionElement;
import com.github.javaparser.javadoc.description.JavadocInlineTag;

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
     * Parse JavaDoc into structured format
     */
    private static JavaDocInfo parseJavaDoc(Javadoc javadoc) {
        JavaDocInfo info = new JavaDocInfo();
        
        // Extract description
        JavadocDescription desc = javadoc.getDescription();
        if (desc != null) {
            info.description = processJavaDocElements(desc, info);
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

