
import org.instrument.DumpObj;
public class Sample {
    private String name;
    private int value;
    
    
@DumpObj
public Sample(String name, int value) {String __objdump_id = org.instrument.DebugDump.newInvocationId();
java.util.Map<String,Object> __objdump_params = new java.util.LinkedHashMap<String,Object>();
__objdump_params.put("param0", name);
__objdump_params.put("param1", value);
org.instrument.DebugDump.writeEntry(this, __objdump_params, __objdump_id);
try {

        this.name = name;
        this.value = value;
    
} finally {
org.instrument.DebugDump.writeExit(this, null, null, __objdump_id);
}
}
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public int getValue() {
        return value;
    }
    
    public void setValue(int value) {
        this.value = value;
    }
    
    
@DumpObj
public String processData(String input, int count) {
        return input + "_" + count + "_" + name;
}
    
    public void printInfo() {
        System.out.println("Name: " + name + ", Value: " + value);
    }
    
    public int calculate(int a, int b, int c) {
        return a * b + c;
    }
    
@DumpObj
public void throwException() throws Exception {
        throw new RuntimeException("Test exception");
}
}
