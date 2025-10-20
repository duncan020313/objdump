package test.inheritance;

import org.objdump.instrumenter.JavaDocExtractor;
import org.objdump.instrumenter.JavaDocExtractor.JavaDocInfo;
import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.MethodDeclaration;

import java.io.File;
import java.util.List;

/**
 * Test class to verify recursive @inheritDoc resolution
 */
public class InheritDocTest {
    
    public static void main(String[] args) {
        System.out.println("=== Testing Recursive @inheritDoc Resolution ===\n");
        
        try {
            // Test Dog.move() method
            testMethodInheritance("Dog", "move");
            
            // Test Dog.makeSound() method  
            testMethodInheritance("Dog", "makeSound");
            
        } catch (Exception e) {
            System.err.println("Test failed: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    private static void testMethodInheritance(String className, String methodName) {
        System.out.println("--- Testing " + className + "." + methodName + "() ---");
        
        try {
            // Parse the class file
            String filePath = "/root/objdump/test_inheritance/" + className + ".java";
            JavaParser parser = new JavaParser();
            ParseResult<CompilationUnit> parseResult = parser.parse(new File(filePath));
            
            if (!parseResult.isSuccessful() || !parseResult.getResult().isPresent()) {
                System.err.println("Failed to parse " + className + ".java");
                return;
            }
            
            CompilationUnit cu = parseResult.getResult().get();
            
            // Find the method
            List<MethodDeclaration> methods = cu.findAll(MethodDeclaration.class);
            MethodDeclaration targetMethod = null;
            
            for (MethodDeclaration method : methods) {
                if (method.getNameAsString().equals(methodName)) {
                    targetMethod = method;
                    break;
                }
            }
            
            if (targetMethod == null) {
                System.err.println("Method " + methodName + " not found in " + className);
                return;
            }
            
            // Extract JavaDoc with inheritance resolution
            JavaDocInfo info = JavaDocExtractor.extractJavaDoc(targetMethod, cu, filePath);
            
            if (info == null) {
                System.out.println("No JavaDoc found for " + className + "." + methodName + "()");
                return;
            }
            
            // Print results
            System.out.println("Description: " + (info.description != null ? info.description : "null"));
            System.out.println("Has @inheritDoc: " + info.hasInheritDoc);
            System.out.println("Description contains @inheritDoc: " + (info.description != null && info.description.contains("{@inheritDoc}")));
            System.out.println("Parameters:");
            for (String param : info.params.keySet()) {
                System.out.println("  @" + param + " " + info.params.get(param));
            }
            System.out.println("Returns: " + (info.returns != null ? info.returns : "null"));
            System.out.println("Throws:");
            for (String throwType : info.throwsInfo.keySet()) {
                System.out.println("  @" + throwType + " " + info.throwsInfo.get(throwType));
            }
            
        } catch (Exception e) {
            System.err.println("Error testing " + className + "." + methodName + ": " + e.getMessage());
            e.printStackTrace();
        }
        
        System.out.println();
    }
}
