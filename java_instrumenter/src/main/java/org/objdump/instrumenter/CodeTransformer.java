package org.objdump.instrumenter;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.Modifier;
import com.github.javaparser.ast.NodeList;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.stmt.*;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * Transforms Java code to add instrumentation
 */
public class CodeTransformer {

    private static final String SELF_ALIAS = "_self";

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
                javadoc = JavaDocExtractor.extractJavaDoc(methodInfo.constructorDeclaration, cu, javaFilePath);
                originalCode = JavaDocExtractor.extractMethodCode(methodInfo.constructorDeclaration);
                methodInfo.fieldFilter = collectFieldFilter(methodInfo.constructorDeclaration);
            } else {
                javadoc = JavaDocExtractor.extractJavaDoc(methodInfo.methodDeclaration, cu, javaFilePath);
                originalCode = JavaDocExtractor.extractMethodCode(methodInfo.methodDeclaration);
                methodInfo.fieldFilter = collectFieldFilter(methodInfo.methodDeclaration);
            }

            results.add(new TransformResult(methodInfo.signature, javadoc, originalCode));
        }

        // Add necessary imports
        addImportsIfNeeded(cu);

        // Instrument each method
        for (MethodExtractor.MethodInfo methodInfo : methodsToInstrument) {
            if (methodInfo.isConstructor) {
                instrumentConstructor(methodInfo);
            } else {
                // Skip abstract methods or interface methods without body
                if (shouldSkipMethod(methodInfo.methodDeclaration)) {
                    System.err.println("Warning: Skipping abstract/interface method without body: " + methodInfo.signature);
                    continue;
                }
                instrumentMethod(methodInfo);
            }
        }

        // Write instrumented code back to file
        try (FileWriter writer = new FileWriter(javaFilePath, StandardCharsets.UTF_8)) {
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
     * Check if a method should be skipped from instrumentation
     * Skip abstract methods or interface methods without default/static modifiers
     */
    private static boolean shouldSkipMethod(MethodDeclaration method) {
        // Skip if method has no body (abstract)
        if (!method.getBody().isPresent()) {
            return true;
        }

        // Check if method is in an interface
        Optional<com.github.javaparser.ast.body.ClassOrInterfaceDeclaration> parentClass =
            method.findAncestor(com.github.javaparser.ast.body.ClassOrInterfaceDeclaration.class);

        if (parentClass.isPresent() && parentClass.get().isInterface()) {
            // Allow default and static methods in interfaces
            if (!method.isDefault() && !method.isStatic()) {
                return true;
            }
        }

        return false;
    }

    /**
     * Instrument a regular method
     */
    private static void instrumentMethod(MethodExtractor.MethodInfo methodInfo) {
        MethodDeclaration method = methodInfo.methodDeclaration;
        // Add @DumpObj annotation if not present
        if (!hasAnnotation(method, "DumpObj")) {
            method.addAnnotation("DumpObj");
        }

        // Get method details
        boolean isStatic = method.isStatic();
        boolean isVoid = method.getType().asString().equals("void");
        String returnType = method.getType().asString();
        List<Parameter> parameters = method.getParameters();
        Map<String, List<String>> fieldFilter = methodInfo.fieldFilter;

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

        // Build field filter map
        newBody.addStatement(createFieldFilterDeclaration());
        if (fieldFilter != null && !fieldFilter.isEmpty()) {
            newBody.addStatement(assignFieldFilterMap());
            for (Statement stmt : populateFieldFilter(fieldFilter)) {
                newBody.addStatement(stmt);
            }
        }

        Expression fieldFilterExpr = new NameExpr("__objdump_fieldFilter");

        // Write entry log
        newBody.addStatement(createEntryCall(isStatic, methodSignature, filePath, fieldFilterExpr));

        // Declare return variable if needed (before any statements)
        if (!isVoid) {
            newBody.addStatement(createReturnVarDeclaration(returnType));
        }

        // Get original body statements
        boolean blockTerminated = false;
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
                filePath,
                fieldFilterExpr
            );

            // Add transformed statements
            for (Statement stmt : transformedStatements) {
                newBody.addStatement(stmt);
            }

            // Check if block is terminated with return/throw
            if (!transformedStatements.isEmpty()) {
                Statement lastStmt = transformedStatements.get(transformedStatements.size() - 1);
                blockTerminated = isTerminatingStatement(lastStmt);
            }
        }

        // Add exit log at end for void methods only if block is not already terminated
        if (isVoid && !blockTerminated) {
            newBody.addStatement(createExitCall(isStatic, null, methodSignature, filePath, fieldFilterExpr));
        }

        method.setBody(newBody);
    }

    /**
     * Instrument a constructor
     */
    private static void instrumentConstructor(MethodExtractor.MethodInfo methodInfo) {
        ConstructorDeclaration constructor = methodInfo.constructorDeclaration;
        // Add @DumpObj annotation if not present
        if (!hasAnnotation(constructor, "DumpObj")) {
            constructor.addAnnotation("DumpObj");
        }

        // Extract constructor signature and file path for instrumentation
        String constructorSignature = getConstructorSignature(constructor);
        String filePath = getCurrentFilePath(constructor);

        List<Parameter> parameters = constructor.getParameters();
        BlockStmt originalBody = constructor.getBody();
        Map<String, List<String>> fieldFilter = methodInfo.fieldFilter;

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
        newBody.addStatement(createFieldFilterDeclaration());
        if (fieldFilter != null && !fieldFilter.isEmpty()) {
            newBody.addStatement(assignFieldFilterMap());
            for (Statement stmt : populateFieldFilter(fieldFilter)) {
                newBody.addStatement(stmt);
            }
        }

        Expression fieldFilterExpr = new NameExpr("__objdump_fieldFilter");

        newBody.addStatement(createEntryCall(false, constructorSignature, filePath, fieldFilterExpr));

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
                filePath,
                fieldFilterExpr
            );
            for (Statement s : transformed) {
                newBody.addStatement(s);
            }
        }

        // Check if block is terminated with return/throw
        boolean blockTerminated = false;
        if (!newBody.getStatements().isEmpty()) {
            Statement lastStmt = newBody.getStatements().get(newBody.getStatements().size() - 1);
            blockTerminated = isTerminatingStatement(lastStmt);
        }

        // Add exit log at end only if block is not already terminated
        if (!blockTerminated) {
            newBody.addStatement(createExitCall(false, null, constructorSignature, filePath, fieldFilterExpr));
        }

        constructor.setBody(newBody);
    }

    /**
     * Check if a statement is a terminating statement (return or throw)
     */
    private static boolean isTerminatingStatement(Statement stmt) {
        if (stmt instanceof ReturnStmt || stmt instanceof ThrowStmt) {
            return true;
        }
        // Check if it's a block that ends with a terminating statement
        if (stmt instanceof BlockStmt) {
            BlockStmt block = (BlockStmt) stmt;
            if (!block.getStatements().isEmpty()) {
                Statement lastStmt = block.getStatements().get(block.getStatements().size() - 1);
                return isTerminatingStatement(lastStmt);
            }
        }
        return false;
    }

    /**
     * Transform statements, handling return and throw statements specially
     */
    private static List<Statement> transformStatementsWithReturns(NodeList<Statement> statements, String returnType, boolean isStatic, boolean isVoid, boolean hasReturnVar, String methodSignature, String filePath, Expression fieldFilterExpr) {
        List<Statement> transformed = new ArrayList<>();

        for (Statement stmt : statements) {
            if (stmt instanceof ReturnStmt) {
                ReturnStmt returnStmt = (ReturnStmt) stmt;

                if (isVoid || !returnStmt.getExpression().isPresent()) {
                    // Void return
                    transformed.add(createExitCall(isStatic, null, methodSignature, filePath, fieldFilterExpr));
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
                    transformed.add(createExitCall(isStatic, "__objdump_ret", methodSignature, filePath, fieldFilterExpr));

                    // Return the variable
                    transformed.add(new ReturnStmt(new NameExpr("__objdump_ret")));
                }
                // Stop processing further statements after return (unreachable code)
                break;
            } else if (stmt instanceof ThrowStmt) {
                // Add exit log before throw
                transformed.add(createExitCall(isStatic, null, methodSignature, filePath, fieldFilterExpr));
                transformed.add(stmt);
                // Stop processing further statements after throw (unreachable code)
                break;
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
                        filePath,
                        fieldFilterExpr
                    );
                    BlockStmt newBlock = new BlockStmt(new NodeList<>(nestedTransformed));
                    transformed.add(newBlock);
                } else if (stmt instanceof IfStmt) {
                    IfStmt ifStmt = (IfStmt) stmt;
                    Statement thenTransformed = transformSingleStatement(ifStmt.getThenStmt(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
                    ifStmt.setThenStmt(thenTransformed);
                    if (ifStmt.getElseStmt().isPresent()) {
                        Statement elseTransformed = transformSingleStatement(ifStmt.getElseStmt().get(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
                        ifStmt.setElseStmt(elseTransformed);
                    }
                    transformed.add(ifStmt);
                } else if (stmt instanceof WhileStmt) {
                    WhileStmt whileStmt = (WhileStmt) stmt;
                    Statement bodyTransformed = transformSingleStatement(whileStmt.getBody(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
                    whileStmt.setBody(bodyTransformed);
                    transformed.add(whileStmt);
                } else if (stmt instanceof ForStmt) {
                    ForStmt forStmt = (ForStmt) stmt;
                    Statement bodyTransformed = transformSingleStatement(forStmt.getBody(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
                    forStmt.setBody(bodyTransformed);
                    transformed.add(forStmt);
                } else if (stmt instanceof DoStmt) {
                    DoStmt doStmt = (DoStmt) stmt;
                    Statement bodyTransformed = transformSingleStatement(doStmt.getBody(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
                    doStmt.setBody(bodyTransformed);
                    transformed.add(doStmt);
                } else if (stmt instanceof ForEachStmt) {
                    ForEachStmt forEachStmt = (ForEachStmt) stmt;
                    Statement bodyTransformed = transformSingleStatement(forEachStmt.getBody(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
                    forEachStmt.setBody(bodyTransformed);
                    transformed.add(forEachStmt);
                } else if (stmt instanceof TryStmt) {
                    TryStmt tryStmt = (TryStmt) stmt;

                    // Transform try block
                    BlockStmt tryBlock = tryStmt.getTryBlock();
                    List<Statement> tryTransformed = transformStatementsWithReturns(
                        tryBlock.getStatements(),
                        returnType,
                        isStatic,
                        isVoid,
                        hasReturnVar,
                        methodSignature,
                        filePath,
                        fieldFilterExpr
                    );
                    tryStmt.setTryBlock(new BlockStmt(new NodeList<>(tryTransformed)));

                    // Transform catch blocks
                    for (com.github.javaparser.ast.stmt.CatchClause catchClause : tryStmt.getCatchClauses()) {
                        BlockStmt catchBlock = catchClause.getBody();
                        List<Statement> catchTransformed = transformStatementsWithReturns(
                            catchBlock.getStatements(),
                            returnType,
                            isStatic,
                            isVoid,
                            hasReturnVar,
                            methodSignature,
                            filePath,
                            fieldFilterExpr
                        );
                        catchClause.setBody(new BlockStmt(new NodeList<>(catchTransformed)));
                    }

                    // Transform finally block if present
                    if (tryStmt.getFinallyBlock().isPresent()) {
                        BlockStmt finallyBlock = tryStmt.getFinallyBlock().get();
                        List<Statement> finallyTransformed = transformStatementsWithReturns(
                            finallyBlock.getStatements(),
                            returnType,
                            isStatic,
                            isVoid,
                            hasReturnVar,
                            methodSignature,
                            filePath,
                            fieldFilterExpr
                        );
                        tryStmt.setFinallyBlock(new BlockStmt(new NodeList<>(finallyTransformed)));
                    }

                    transformed.add(tryStmt);
                } else {
                    transformed.add(stmt);
                }
            }
        }

        return transformed;
    }

    private static Statement transformSingleStatement(Statement stmt, String returnType, boolean isStatic, boolean isVoid, boolean hasReturnVar, String methodSignature, String filePath, Expression fieldFilterExpr) {
        if (stmt instanceof BlockStmt) {
            BlockStmt block = (BlockStmt) stmt;
            List<Statement> transformed = transformStatementsWithReturns(block.getStatements(), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
            return new BlockStmt(new NodeList<>(transformed));
        } else if (stmt instanceof ReturnStmt || stmt instanceof ThrowStmt) {
            // Handle single return/throw statement (not in a block)
            List<Statement> transformed = transformStatementsWithReturns(new NodeList<>(stmt), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
            // Wrap in block if multiple statements were generated
            if (transformed.size() == 1) {
                return transformed.get(0);
            } else {
                return new BlockStmt(new NodeList<>(transformed));
            }
        } else if (stmt instanceof IfStmt || stmt instanceof WhileStmt || stmt instanceof ForStmt ||
                   stmt instanceof DoStmt || stmt instanceof ForEachStmt || stmt instanceof TryStmt) {
            // These need recursive transformation
            List<Statement> transformed = transformStatementsWithReturns(new NodeList<>(stmt), returnType, isStatic, isVoid, hasReturnVar, methodSignature, filePath, fieldFilterExpr);
            if (transformed.size() == 1) {
                return transformed.get(0);
            } else {
                return new BlockStmt(new NodeList<>(transformed));
            }
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
     * Sanitizes the parameter name and falls back to "param{index}" if sanitization results in empty string
     */
    private static Statement createParamPut(int index, String paramName) {
        String sanitized = sanitizeParamName(paramName);
        // Fall back to "param{index}" if sanitization results in empty string
        String finalName = sanitized.isEmpty() ? ("param" + index) : sanitized;

        return new ExpressionStmt(
            new MethodCallExpr(
                new NameExpr("__objdump_params"),
                "put",
                new NodeList<>(
                    new StringLiteralExpr(finalName),
                    new NameExpr(finalName)
                )
            )
        );
    }

    private static Statement createFieldFilterDeclaration() {
        com.github.javaparser.ast.type.ClassOrInterfaceType mapType = new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "java.util.Map");
        com.github.javaparser.ast.type.ClassOrInterfaceType listType = new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "java.util.List");
        listType.setTypeArguments(new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "String"));
        mapType.setTypeArguments(new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "String"), listType);
        VariableDeclarator var = new VariableDeclarator(mapType, "__objdump_fieldFilter", new NullLiteralExpr());
        return new ExpressionStmt(new VariableDeclarationExpr(var));
    }

    private static Statement assignFieldFilterMap() {
        com.github.javaparser.ast.type.ClassOrInterfaceType mapImplType = new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "java.util.LinkedHashMap");
        com.github.javaparser.ast.type.ClassOrInterfaceType listType = new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "java.util.List");
        listType.setTypeArguments(new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "String"));
        mapImplType.setTypeArguments(new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "String"), listType);
        return new ExpressionStmt(
            new AssignExpr(
                new NameExpr("__objdump_fieldFilter"),
                new ObjectCreationExpr(null, mapImplType, new NodeList<>()),
                AssignExpr.Operator.ASSIGN
            )
        );
    }

    private static List<Statement> populateFieldFilter(Map<String, List<String>> fieldFilter) {
        List<Statement> statements = new ArrayList<>();
        int index = 0;
        for (Map.Entry<String, List<String>> entry : fieldFilter.entrySet()) {
            String alias = entry.getKey();
            List<String> paths = entry.getValue();
            if (paths == null || paths.isEmpty()) {
                continue;
            }
            String listVarName = "__objdump_fields_" + index++;

            com.github.javaparser.ast.type.ClassOrInterfaceType listType = new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "java.util.List");
            listType.setTypeArguments(new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "String"));
            com.github.javaparser.ast.type.ClassOrInterfaceType listImplType = new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "java.util.ArrayList");
            listImplType.setTypeArguments(new com.github.javaparser.ast.type.ClassOrInterfaceType(null, "String"));

            BlockStmt block = new BlockStmt();
            block.addStatement(new ExpressionStmt(new VariableDeclarationExpr(
                new VariableDeclarator(
                    listType,
                    listVarName,
                    new ObjectCreationExpr(null, listImplType, new NodeList<>())
                )
            )));

            for (String path : paths) {
                block.addStatement(new ExpressionStmt(
                    new MethodCallExpr(
                        new NameExpr(listVarName),
                        "add",
                        new NodeList<>(new StringLiteralExpr(path))
                    )
                ));
            }

            block.addStatement(new ExpressionStmt(
                new MethodCallExpr(
                    new NameExpr("__objdump_fieldFilter"),
                    "put",
                    new NodeList<>(
                        new StringLiteralExpr(alias),
                        new NameExpr(listVarName)
                    )
                )
            ));

            statements.add(block);
        }
        return statements;
    }

    /**
     * Create entry call: DebugDump.writeEntry(this/null, params, id, methodSig, filePath);
     */
    private static Statement createEntryCall(boolean isStatic, String methodSig, String filePath, Expression fieldFilterExpr) {
        return new ExpressionStmt(
            new MethodCallExpr(
                new NameExpr("DebugDump"),
                "writeEntry",
                new NodeList<>(
                    isStatic ? new NullLiteralExpr() : new ThisExpr(),
                    new NameExpr("__objdump_params"),
                    new NameExpr("__objdump_id"),
                    new StringLiteralExpr(methodSig),
                    new StringLiteralExpr(filePath),
                    fieldFilterExpr
                )
            )
        );
    }

    /**
     * Create exit call: DebugDump.writeExit(this/null, null, retValue, id, methodSig, filePath);
     */
    private static Statement createExitCall(boolean isStatic, String retVarName, String methodSig, String filePath, Expression fieldFilterExpr) {
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
                    new StringLiteralExpr(filePath),
                    fieldFilterExpr
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

    private static Map<String, List<String>> collectFieldFilter(MethodDeclaration method) {
        if (method == null || !method.getBody().isPresent()) {
            return Collections.emptyMap();
        }
        return collectFieldFilterInternal(method, method.getBody().get(), method.getParameters(), method.isStatic());
    }

    private static Map<String, List<String>> collectFieldFilter(ConstructorDeclaration constructor) {
        if (constructor == null) {
            return Collections.emptyMap();
        }
        return collectFieldFilterInternal(constructor, constructor.getBody(), constructor.getParameters(), false);
    }

    private static Map<String, List<String>> collectFieldFilterInternal(com.github.javaparser.ast.Node node, BlockStmt body, List<Parameter> parameters, boolean isStatic) {
        if (body == null) {
            return Collections.emptyMap();
        }

        Map<String, LinkedHashSet<String>> filter = new LinkedHashMap<>();
        Map<String, String> paramAliasMap = buildParamAliasMap(parameters);

        if (!isStatic) {
            filter.put(SELF_ALIAS, new LinkedHashSet<>());
        }
        for (int i = 0; i < parameters.size(); i++) {
            String alias = paramAliasMap.get(parameters.get(i).getNameAsString());
            if (alias != null && !alias.isEmpty()) {
                filter.putIfAbsent(alias, new LinkedHashSet<>());
            }
        }

        Set<String> classFieldNames = getClassFieldNames(node);
        Set<String> localNames = collectLocalVariableNames(body, parameters);

        body.findAll(FieldAccessExpr.class).forEach(expr -> {
            resolveFieldAccess(expr, paramAliasMap).ifPresent(fieldPath -> addFieldPath(filter, fieldPath));
        });

        if (!filter.containsKey(SELF_ALIAS)) {
            filter.put(SELF_ALIAS, new LinkedHashSet<>());
        }

        body.findAll(NameExpr.class).forEach(nameExpr -> {
            String name = nameExpr.getNameAsString();
            if (!classFieldNames.contains(name)) {
                return;
            }
            if (localNames.contains(name)) {
                return;
            }
            LinkedHashSet<String> paths = filter.get(SELF_ALIAS);
            if (paths != null) {
                paths.add(name);
            }
        });

        return finalizeFieldFilter(filter);
    }

    private static Map<String, String> buildParamAliasMap(List<Parameter> parameters) {
        Map<String, String> aliasMap = new LinkedHashMap<>();
        for (int i = 0; i < parameters.size(); i++) {
            Parameter parameter = parameters.get(i);
            String originalName = parameter.getNameAsString();
            aliasMap.put(originalName, determineParamKey(i, originalName));
        }
        return aliasMap;
    }

    private static String determineParamKey(int index, String paramName) {
        String sanitized = sanitizeParamName(paramName);
        return sanitized.isEmpty() ? ("param" + index) : sanitized;
    }

    private static Set<String> getClassFieldNames(Node node) {
        Optional<com.github.javaparser.ast.body.ClassOrInterfaceDeclaration> classDecl =
            node.findAncestor(com.github.javaparser.ast.body.ClassOrInterfaceDeclaration.class);
        if (!classDecl.isPresent()) {
            return Collections.emptySet();
        }
        Set<String> names = new HashSet<>();
        for (FieldDeclaration field : classDecl.get().getFields()) {
            for (VariableDeclarator var : field.getVariables()) {
                names.add(var.getNameAsString());
            }
        }
        return names;
    }

    private static Set<String> collectLocalVariableNames(BlockStmt body, List<Parameter> parameters) {
        Set<String> locals = new HashSet<>();
        Set<String> parameterNames = new HashSet<>();
        for (Parameter parameter : parameters) {
            parameterNames.add(parameter.getNameAsString());
        }

        body.findAll(VariableDeclarator.class).forEach(var -> locals.add(var.getNameAsString()));
        body.findAll(Parameter.class).forEach(param -> {
            String name = param.getNameAsString();
            if (!parameterNames.contains(name)) {
                locals.add(name);
            }
        });

        return locals;
    }

    private static Optional<FieldPath> resolveFieldAccess(FieldAccessExpr expr, Map<String, String> paramAliasMap) {
        List<String> segments = new ArrayList<>();
        Expression current = expr;
        while (current instanceof FieldAccessExpr) {
            FieldAccessExpr fieldAccessExpr = (FieldAccessExpr) current;
            segments.add(0, fieldAccessExpr.getNameAsString());
            Expression scope = fieldAccessExpr.getScope();
            if (scope instanceof ThisExpr) {
                return Optional.of(new FieldPath(SELF_ALIAS, segments));
            }
            if (scope instanceof com.github.javaparser.ast.expr.SuperExpr) {
                return Optional.of(new FieldPath(SELF_ALIAS, segments));
            }
            if (scope instanceof NameExpr) {
                String scopeName = ((NameExpr) scope).getNameAsString();
                String alias = paramAliasMap.get(scopeName);
                if (alias != null) {
                    return Optional.of(new FieldPath(alias, segments));
                }
                return Optional.empty();
            }
            if (scope instanceof FieldAccessExpr) {
                current = scope;
                continue;
            }
            return Optional.empty();
        }
        return Optional.empty();
    }

    private static void addFieldPath(Map<String, LinkedHashSet<String>> filter, FieldPath fieldPath) {
        LinkedHashSet<String> paths = filter.get(fieldPath.alias);
        if (paths == null) {
            return;
        }
        paths.add(String.join(".", fieldPath.segments));
    }

    private static Map<String, List<String>> finalizeFieldFilter(Map<String, LinkedHashSet<String>> raw) {
        Map<String, List<String>> result = new LinkedHashMap<>();
        for (Map.Entry<String, LinkedHashSet<String>> entry : raw.entrySet()) {
            LinkedHashSet<String> paths = entry.getValue();
            if (paths == null || paths.isEmpty()) {
                continue;
            }
            result.put(entry.getKey(), new ArrayList<>(paths));
        }
        return result.isEmpty() ? Collections.emptyMap() : result;
    }

    private static final class FieldPath {
        private final String alias;
        private final List<String> segments;

        private FieldPath(String alias, List<String> segments) {
            this.alias = alias;
            this.segments = segments;
        }
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
        // 1. Collapse whitespace (including newlines)
        String normalized = signature.replaceAll("\\s+", " ").trim();
        // 2. Remove special characters (keep only alphanumeric, spaces, parens, commas, brackets)
        normalized = normalized.replaceAll("[^a-zA-Z0-9\\s(),<>\\{\\}\\[\\]]", "");
        return normalized;
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
            sig.append(" ").append(sanitizeParamName(param.getName().asString()));
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
     * Sanitize parameter name to conform to Java identifier rules: [a-zA-Z_][a-zA-Z0-9_]*
     * Returns empty string if no valid characters remain (caller should handle fallback)
     */
    private static String sanitizeParamName(String paramName) {
        // Remove all characters not in [a-zA-Z0-9_]
        String sanitized = paramName.replaceAll("[^a-zA-Z0-9_]", "");
        // Remove leading digits to ensure it starts with [a-zA-Z_]
        sanitized = sanitized.replaceFirst("^[0-9]+", "");
        return sanitized;
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

