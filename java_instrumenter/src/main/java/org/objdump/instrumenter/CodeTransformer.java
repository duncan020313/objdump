package org.objdump.instrumenter;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.Modifier;
import com.github.javaparser.ast.NodeList;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.stmt.*;
import com.github.javaparser.ast.type.Type;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/**
 * Transforms Java code to add instrumentation
 */
public class CodeTransformer {
    
    /**
     * Result of code transformation
     */
    public static class TransformResult {
        public String signature;
        public JavaDocExtractor.JavaDocInfo javadoc;
        public String code;
        
        public TransformResult(String signature, JavaDocExtractor.JavaDocInfo javadoc, String code) {
            this.signature = signature;
            this.javadoc = javadoc;
            this.code = code;
        }
    }
    
    /**
     * Instrument a Java file by transforming target methods
     */
    public static List<TransformResult> instrumentJavaFile(String javaFilePath, List<String> targetSignatures) throws IOException {
        JavaParser parser = new JavaParser();
        ParseResult<CompilationUnit> parseResult = parser.parse(new File(javaFilePath));
        
        if (!parseResult.isSuccessful() || !parseResult.getResult().isPresent()) {
            throw new IOException("Failed to parse Java file: " + javaFilePath);
        }
        
        CompilationUnit cu = parseResult.getResult().get();
        
        // Find methods to instrument from the SAME CompilationUnit
        // Normalize target signatures to handle whitespace differences
        Set<String> targetSet = new HashSet<>();
        for (String signature : targetSignatures) {
            targetSet.add(normalizeSignature(signature));
        }
        List<MethodExtractor.MethodInfo> methodsToInstrument = new ArrayList<>();
        
        // Find methods with matching signatures
        cu.findAll(MethodDeclaration.class).forEach(method -> {
            String signature = getMethodSignature(method);
            String normalizedSignature = normalizeSignature(signature);
            if (targetSet.contains(normalizedSignature)) {
                methodsToInstrument.add(new MethodExtractor.MethodInfo(signature, method));
            }
        });
        
        // Find constructors with matching signatures
        cu.findAll(ConstructorDeclaration.class).forEach(constructor -> {
            String signature = getConstructorSignature(constructor);
            String normalizedSignature = normalizeSignature(signature);
            if (targetSet.contains(normalizedSignature)) {
                methodsToInstrument.add(new MethodExtractor.MethodInfo(signature, constructor));
            }
        });
        
        // Check for partial matches and report missing signatures
        if (!methodsToInstrument.isEmpty() && methodsToInstrument.size() < targetSignatures.size()) {
            Set<String> foundSignatures = new HashSet<>();
            for (MethodExtractor.MethodInfo methodInfo : methodsToInstrument) {
                foundSignatures.add(methodInfo.signature);
            }
            
            List<String> missingSignatures = new ArrayList<>();
            for (String targetSig : targetSignatures) {
                if (!foundSignatures.contains(targetSig)) {
                    missingSignatures.add(targetSig);
                }
            }
            
            if (!missingSignatures.isEmpty()) {
                System.err.println("Warning: Some target signatures were not found in " + javaFilePath + ":");
                for (String missing : missingSignatures) {
                    System.err.println("  - " + missing);
                }
                System.err.println("Found " + methodsToInstrument.size() + " out of " + targetSignatures.size() + " requested signatures.");
            }
        }
        
        if (methodsToInstrument.isEmpty()) {
            // Collect all available method signatures for debugging
            List<String> availableMethods = new ArrayList<>();
            cu.findAll(MethodDeclaration.class).forEach(method -> {
                availableMethods.add(getMethodSignature(method));
            });
            cu.findAll(ConstructorDeclaration.class).forEach(constructor -> {
                availableMethods.add(getConstructorSignature(constructor));
            });
            
            // Create detailed error message
            StringBuilder errorMsg = new StringBuilder();
            errorMsg.append("No matching methods/constructors found in file: ").append(javaFilePath).append("\n");
            errorMsg.append("Requested signatures:\n");
            for (String sig : targetSignatures) {
                errorMsg.append("  - ").append(sig).append("\n");
            }
            errorMsg.append("Available signatures in file:\n");
            for (String sig : availableMethods) {
                errorMsg.append("  - ").append(sig).append("\n");
            }
            
            throw new IOException(errorMsg.toString());
        }
        
        List<TransformResult> results = new ArrayList<>();
        
        // Collect method info before instrumentation
        for (MethodExtractor.MethodInfo methodInfo : methodsToInstrument) {
            JavaDocExtractor.JavaDocInfo javadoc;
            String originalCode;
            
            if (methodInfo.isConstructor) {
                javadoc = JavaDocExtractor.extractJavaDoc(methodInfo.constructorDeclaration);
                originalCode = JavaDocExtractor.extractMethodCode(methodInfo.constructorDeclaration);
            } else {
                javadoc = JavaDocExtractor.extractJavaDoc(methodInfo.methodDeclaration);
                originalCode = JavaDocExtractor.extractMethodCode(methodInfo.methodDeclaration);
            }
            
            results.add(new TransformResult(methodInfo.signature, javadoc, originalCode));
        }
        
        // Add necessary imports
        addImportsIfNeeded(cu);
        
        // Instrument each method
        for (MethodExtractor.MethodInfo methodInfo : methodsToInstrument) {
            if (methodInfo.isConstructor) {
                instrumentConstructor(methodInfo.constructorDeclaration);
            } else {
                instrumentMethod(methodInfo.methodDeclaration);
            }
        }
        
        // Write instrumented code back to file
        try (FileWriter writer = new FileWriter(javaFilePath)) {
            writer.write(cu.toString());
        }
        
        return results;
    }
    
    /**
     * Add necessary imports to the compilation unit
     */
    private static void addImportsIfNeeded(CompilationUnit cu) {
        boolean hasDumpObj = false;
        boolean hasDebugDump = false;
        
        for (ImportDeclaration imp : cu.getImports()) {
            String impName = imp.getNameAsString();
            if (impName.equals("org.instrument.DumpObj")) {
                hasDumpObj = true;
            }
            if (impName.equals("org.instrument.DebugDump")) {
                hasDebugDump = true;
            }
        }
        
        if (!hasDumpObj) {
            cu.addImport("org.instrument.DumpObj");
        }
        if (!hasDebugDump) {
            cu.addImport("org.instrument.DebugDump");
        }
    }
    
    /**
     * Instrument a regular method
     */
    private static void instrumentMethod(MethodDeclaration method) {
        // Add @DumpObj annotation if not present
        if (!hasAnnotation(method, "DumpObj")) {
            method.addAnnotation("DumpObj");
        }
        
        // Get method details
        boolean isStatic = method.isStatic();
        boolean isVoid = method.getType().asString().equals("void");
        String returnType = method.getType().asString();
        List<Parameter> parameters = method.getParameters();
        
        // Extract method signature and file path for instrumentation
        String methodSignature = getMethodSignature(method);
        String filePath = getCurrentFilePath(method);
        
        // Create new method body
        BlockStmt newBody = new BlockStmt();
        
        // Generate invocation ID
        newBody.addStatement(createIdDeclaration());
        
        // Generate parameter map
        newBody.addStatement(createParamMapDeclaration());
        for (int i = 0; i < parameters.size(); i++) {
            newBody.addStatement(createParamPut(i, parameters.get(i).getNameAsString()));
        }
        
        // Write entry log
        newBody.addStatement(createEntryCall(isStatic, methodSignature, filePath));
        
        // Declare return variable if needed (before any statements)
        if (!isVoid) {
            newBody.addStatement(createReturnVarDeclaration(returnType));
        }
        
        // Get original body statements
        if (method.getBody().isPresent()) {
            BlockStmt originalBody = method.getBody().get();
            
            // Transform return statements
            List<Statement> transformedStatements = transformStatementsWithReturns(
                originalBody.getStatements(), 
                returnType, 
                isStatic, 
                isVoid,
                !isVoid,  // hasReturnVar = true if not void
                methodSignature,
                filePath
            );
            
            // Add transformed statements
            for (Statement stmt : transformedStatements) {
                newBody.addStatement(stmt);
            }
        }
        
        // Add exit log at end for void methods (if not already there)
        if (isVoid) {
            newBody.addStatement(createExitCall(isStatic, null, methodSignature, filePath));
        }
        
        method.setBody(newBody);
    }
    
    /**
     * Instrument a constructor
     */
    private static void instrumentConstructor(ConstructorDeclaration constructor) {
        // Add @DumpObj annotation if not present
        if (!hasAnnotation(constructor, "DumpObj")) {
            constructor.addAnnotation("DumpObj");
        }
        
        // Extract constructor signature and file path for instrumentation
        String constructorSignature = getConstructorSignature(constructor);
        String filePath = getCurrentFilePath(constructor);
        
        List<Parameter> parameters = constructor.getParameters();
        BlockStmt originalBody = constructor.getBody();
        
        // Create new body
        BlockStmt newBody = new BlockStmt();
        
        // Check for super()/this() call
        Statement firstStmt = null;
        boolean hasSuperOrThis = false;
        if (!originalBody.getStatements().isEmpty()) {
            firstStmt = originalBody.getStatements().get(0);
            if (firstStmt instanceof ExpressionStmt) {
                Expression expr = ((ExpressionStmt) firstStmt).getExpression();
                if (expr instanceof MethodCallExpr) {
                    String methodName = ((MethodCallExpr) expr).getNameAsString();
                    if (methodName.equals("super") || methodName.equals("this")) {
                        hasSuperOrThis = true;
                        newBody.addStatement(firstStmt);
                    }
                }
            } else if (firstStmt instanceof ExplicitConstructorInvocationStmt) {
                hasSuperOrThis = true;
                newBody.addStatement(firstStmt);
            }
        }
        
        // Add instrumentation
        newBody.addStatement(createIdDeclaration());
        newBody.addStatement(createParamMapDeclaration());
        for (int i = 0; i < parameters.size(); i++) {
            newBody.addStatement(createParamPut(i, parameters.get(i).getNameAsString()));
        }
        newBody.addStatement(createEntryCall(false, constructorSignature, filePath));
        
        // Add remaining statements
        int startIdx = hasSuperOrThis ? 1 : 0;
        for (int i = startIdx; i < originalBody.getStatements().size(); i++) {
            Statement stmt = originalBody.getStatements().get(i);
            List<Statement> transformed = transformStatementsWithReturns(
                new NodeList<>(stmt), 
                "void", 
                false, 
                true,
                false,  // constructors don't need return var
                constructorSignature,
                filePath
            );
            for (Statement s : transformed) {
                newBody.addStatement(s);
            }
        }
        
        // Add exit log at end
        newBody.addStatement(createExitCall(false, null, constructorSignature, filePath));
        
        constructor.setBody(newBody);
    }
    
    /**
     * Transform statements, handling return statements specially
     */
    private static List<Statement> transformStatementsWithReturns(NodeList<Statement> statements, String returnType, boolean isStatic, boolean isVoid, boolean hasReturnVar, String methodSignature, String filePath) {
        List<Statement> transformed = new ArrayList<>();
        
        for (Statement stmt : statements) {
            if (stmt instanceof ReturnStmt) {
                ReturnStmt returnStmt = (ReturnStmt) stmt;
                
                if (isVoid || !returnStmt.getExpression().isPresent()) {
                    // Void return
                    transformed.add(createExitCall(isStatic, null, methodSignature, filePath));
                    transformed.add(returnStmt);
                } else {
                    // Return with expression - variable already declared at method level
                    Expression returnExpr = returnStmt.getExpression().get();
                    
                    // Assign to return variable
                    transformed.add(new ExpressionStmt(
                        new AssignExpr(
                            new NameExpr("__objdump_ret"),
                            returnExpr,
                            AssignExpr.Operator.ASSIGN
                        )
                    ));
                    
                    // Write exit log
                    transformed.add(createExitCall(isStatic, "__objdump_ret", methodSignature, filePath));
                    
                    // Return the variable
                    transformed.add(new ReturnStmt(new NameExpr("__objdump_ret")));
                }
            } else {
                // Recursively transform nested blocks
                if (stmt instanceof BlockStmt) {
                    BlockStmt block = (BlockStmt) stmt;
                    List<Statement> nestedTransformed = transformStatementsWithReturns(
                        block.getStatements(), 
                        returnType, 
                        isStatic, 
                        isVoid,
                        hasReturnVar,
                        methodSignature,
                        filePath
                    );
                    BlockStmt newBlock = new BlockStmt(new NodeList<>(nestedTransformed));
                    transformed.add(newBlock);
                } else if (stmt instanceof IfStmt) {
                    IfStmt ifStmt = (IfStmt) stmt;
                    Statement thenTransformed = transformSingleStatement(ifStmt.getThenStmt(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath);
                    ifStmt.setThenStmt(thenTransformed);
                    if (ifStmt.getElseStmt().isPresent()) {
                        Statement elseTransformed = transformSingleStatement(ifStmt.getElseStmt().get(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath);
                        ifStmt.setElseStmt(elseTransformed);
                    }
                    transformed.add(ifStmt);
                } else if (stmt instanceof ForStmt || stmt instanceof WhileStmt || stmt instanceof DoStmt || stmt instanceof ForEachStmt) {
                    // Transform loop bodies
                    transformed.add(stmt);
                } else if (stmt instanceof TryStmt) {
                    // Handle try-catch blocks
                    transformed.add(stmt);
                } else {
                    transformed.add(stmt);
                }
            }
        }
        
        return transformed;
    }
    
    private static Statement transformSingleStatement(Statement stmt, String returnType, boolean isStatic, boolean isVoid, boolean hasReturnVar, String methodSignature, String filePath) {
        if (stmt instanceof BlockStmt) {
            BlockStmt block = (BlockStmt) stmt;
            List<Statement> transformed = transformStatementsWithReturns(block.getStatements(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath);
            return new BlockStmt(new NodeList<>(transformed));
        }
        return stmt;
    }
    
    /**
     * Create invocation ID declaration: String __objdump_id = DebugDump.newInvocationId();
     */
    private static Statement createIdDeclaration() {
        VariableDeclarator idVar = new VariableDeclarator(
            new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "String"),
            "__objdump_id",
            new MethodCallExpr(
                new NameExpr("DebugDump"),
                "newInvocationId"
            )
        );
        return new ExpressionStmt(
            new VariableDeclarationExpr(idVar, Modifier.finalModifier())
        );
    }
    
    /**
     * Create parameter map declaration
     */
    private static Statement createParamMapDeclaration() {
        VariableDeclarator mapVar = new VariableDeclarator(
            new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "java.util.Map"),
            "__objdump_params",
            new ObjectCreationExpr(
                null,
                new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "java.util.LinkedHashMap"),
                new NodeList<>()
            )
        );
        return new ExpressionStmt(new VariableDeclarationExpr(mapVar));
    }
    
    /**
     * Create parameter put statement
     */
    private static Statement createParamPut(int index, String paramName) {
        return new ExpressionStmt(
            new MethodCallExpr(
                new NameExpr("__objdump_params"),
                "put",
                new NodeList<>(
                    new StringLiteralExpr(paramName),
                    new NameExpr(paramName)
                )
            )
        );
    }
    
    /**
     * Create entry call: DebugDump.writeEntry(this/null, params, id, methodSig, filePath);
     */
    private static Statement createEntryCall(boolean isStatic, String methodSig, String filePath) {
        return new ExpressionStmt(
            new MethodCallExpr(
                new NameExpr("DebugDump"),
                "writeEntry",
                new NodeList<>(
                    isStatic ? new NullLiteralExpr() : new ThisExpr(),
                    new NameExpr("__objdump_params"),
                    new NameExpr("__objdump_id"),
                    new StringLiteralExpr(methodSig),
                    new StringLiteralExpr(filePath)
                )
            )
        );
    }
    
    /**
     * Create exit call: DebugDump.writeExit(this/null, null, retValue, id, methodSig, filePath);
     */
    private static Statement createExitCall(boolean isStatic, String retVarName, String methodSig, String filePath) {
        Expression retExpr;
        if (retVarName != null) {
            retExpr = new CastExpr(
                new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "Object"),
                new NameExpr(retVarName)
            );
        } else {
            retExpr = new NullLiteralExpr();
        }
        
        return new ExpressionStmt(
            new MethodCallExpr(
                new NameExpr("DebugDump"),
                "writeExit",
                new NodeList<>(
                    isStatic ? new NullLiteralExpr() : new ThisExpr(),
                    new NullLiteralExpr(),
                    retExpr,
                    new NameExpr("__objdump_id"),
                    new StringLiteralExpr(methodSig),
                    new StringLiteralExpr(filePath)
                )
            )
        );
    }
    
    /**
     * Create return variable declaration
     */
    private static Statement createReturnVarDeclaration(String returnType) {
        VariableDeclarator retVar = new VariableDeclarator(
            new com.github.javaparser.ast.type.ClassOrInterfaceType(null, returnType),
            "__objdump_ret"
        );
        return new ExpressionStmt(new VariableDeclarationExpr(retVar));
    }
    
    /**
     * Check if a method has a specific annotation
     */
    private static boolean hasAnnotation(MethodDeclaration method, String annotationName) {
        return method.getAnnotations().stream()
            .anyMatch(a -> a.getNameAsString().equals(annotationName));
    }
    
    /**
     * Check if a constructor has a specific annotation
     */
    private static boolean hasAnnotation(ConstructorDeclaration constructor, String annotationName) {
        return constructor.getAnnotations().stream()
            .anyMatch(a -> a.getNameAsString().equals(annotationName));
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
        sig.append(method.getType().asString()).append(" ");
        sig.append(method.getName().asString());
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
            sig.append(" ").append(param.getName().asString());
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
        sig.append(constructor.getName().asString());
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
            sig.append(" ").append(param.getName().asString());
            first = false;
        }
        sig.append(")");
        return sig.toString();
    }
    
    /**
     * Get the current file path for instrumentation
     */
    private static String getCurrentFilePath(MethodDeclaration method) {
        // Get the compilation unit to find the package and class name
        Optional<CompilationUnit> cu = method.findAncestor(CompilationUnit.class);
        if (cu.isPresent()) {
            CompilationUnit compilationUnit = cu.get();
            StringBuilder path = new StringBuilder();
            
            // Add package name if present
            if (compilationUnit.getPackageDeclaration().isPresent()) {
                String packageName = compilationUnit.getPackageDeclaration().get().getNameAsString();
                path.append(packageName.replace('.', '/')).append('/');
            }
            
            // Add class name
            Optional<String> className = compilationUnit.findFirst(com.github.javaparser.ast.body.ClassOrInterfaceDeclaration.class)
                .map(com.github.javaparser.ast.body.ClassOrInterfaceDeclaration::getNameAsString);
            if (className.isPresent()) {
                path.append(className.get()).append(".java");
            } else {
                path.append("Unknown.java");
            }
            
            return path.toString();
        }
        
        return "Unknown.java";
    }
    
    /**
     * Get the current file path for instrumentation (constructor version)
     */
    private static String getCurrentFilePath(ConstructorDeclaration constructor) {
        // Get the compilation unit to find the package and class name
        Optional<CompilationUnit> cu = constructor.findAncestor(CompilationUnit.class);
        if (cu.isPresent()) {
            CompilationUnit compilationUnit = cu.get();
            StringBuilder path = new StringBuilder();
            
            // Add package name if present
            if (compilationUnit.getPackageDeclaration().isPresent()) {
                String packageName = compilationUnit.getPackageDeclaration().get().getNameAsString();
                path.append(packageName.replace('.', '/')).append('/');
            }
            
            // Add class name
            Optional<String> className = compilationUnit.findFirst(com.github.javaparser.ast.body.ClassOrInterfaceDeclaration.class)
                .map(com.github.javaparser.ast.body.ClassOrInterfaceDeclaration::getNameAsString);
            if (className.isPresent()) {
                path.append(className.get()).append(".java");
            } else {
                path.append("Unknown.java");
            }
            
            return path.toString();
        }
        
        return "Unknown.java";
    }
}

