package yzygitzh.droidcc;

/**
 * Created by yzy on 5/6/17.
 */

public class PermRuleContent {
    private String mPermName;
    private boolean mStatus;
    public PermRuleContent(String permName, boolean status) {
        mPermName = permName;
        mStatus = status;
    }
    public String getPermName() {
        return mPermName;
    }
    public boolean getStatus() {
        return mStatus;
    }
}