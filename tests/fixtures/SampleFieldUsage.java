public class SampleFieldUsage {
    private String name;
    private SampleFieldUsageProfile profile;

    public String compute(SampleFieldUsageUser user) {
        if (user == null) {
            return name;
        }

        if (profile == null && user.profile != null) {
            profile = user.profile;
        }

        if (this.name == null && user.profile != null) {
            this.name = user.profile.name;
        }

        String email = "";
        if (user.profile != null) {
            email = user.profile.email;
        }

        if (this.profile != null) {
            email = this.profile.email;
        }

        return email + ":" + name;
    }
}

class SampleFieldUsageUser {
    SampleFieldUsageProfile profile;
}

class SampleFieldUsageProfile {
    String name;
    String email;
}


