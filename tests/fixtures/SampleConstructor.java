public class SampleConstructor {
    private String name;
    private int value;
    
    public SampleConstructor() {
        this("default", 0);
    }
    
    public SampleConstructor(String name) {
        this(name, 0);
    }
    
    public SampleConstructor(String name, int value) {
        this.name = name;
        this.value = value;
    }
    
    public String getName() {
        return name;
    }
    
    public int getValue() {
        return value;
    }
}
