public class TestParamNames {
    public String testMethod(String input, int count, boolean flag) {
        return input + "_" + count + "_" + flag;
    }
    
    public static void main(String[] args) {
        TestParamNames obj = new TestParamNames();
        String result = obj.testMethod("test", 123, true);
        System.out.println("Result: " + result);
    }
}
