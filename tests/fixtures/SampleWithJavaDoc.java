public class SampleWithJavaDoc {
    private String data;
    
    /**
     * Constructor for SampleWithJavaDoc.
     * Creates a new instance with the given data.
     * 
     * @param data the initial data value
     */
    public SampleWithJavaDoc(String data) {
        this.data = data;
    }
    
    /**
     * Processes the input string with a multiplier.
     * This method concatenates the input with the internal data
     * and repeats it based on the count parameter.
     * 
     * @param input the input string to process
     * @param count number of times to repeat
     * @return the processed string result
     * @throws IllegalArgumentException if count is negative
     */
    public String processData(String input, int count) {
        if (count < 0) {
            throw new IllegalArgumentException("Count must be non-negative");
        }
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < count; i++) {
            result.append(input).append(data);
        }
        return result.toString();
    }
    
    /**
     * Simple getter without parameters.
     * 
     * @return the current data value
     */
    public String getData() {
        return data;
    }
    
    // Method without JavaDoc
    public void setData(String data) {
        this.data = data;
    }
}

