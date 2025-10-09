public class SampleStatic {
    private static String staticField = "static";
    
    public static String processStatic(String input, int count) {
        return input + "_" + count + "_" + staticField;
    }
    
    public static void printStatic(String message) {
        System.out.println("Static: " + message);
    }
    
    public static int calculateStatic(int a, int b) {
        return a * b;
    }
    
    public String instanceMethod(String input) {
        return "instance_" + input;
    }
}
