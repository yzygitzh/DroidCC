package yzygitzh.droidcc;

/**
 * Created by yzy on 5/6/17.
 */

public class PermRuleContent {
    private static String UI_PERMRULE = "ui_perm_rule";
    private static String START_PERMRULE = "start_perm_rule";

    private String mPermName;
    private String mType;

    private String mPackageName;

    private String mViewCtxStr;
    private String mViewInfoStr;

    boolean mStatus;

    public PermRuleContent(String packageName, String permName) {
        mType = START_PERMRULE;
        mPackageName = packageName;
        mPermName = permName;
    }

    public PermRuleContent(String viewCtxStr, String viewInfoStr, String permName) {
        mType = UI_PERMRULE;
        mViewCtxStr = viewCtxStr;
        mViewInfoStr = viewInfoStr;
        mPermName = permName;
    }

    public String getPermName() {
        return mPermName;
    }

    public boolean getStatus() {
        if (mType == START_PERMRULE) {
            mStatus = Utils.getStartPermRuleStatus(mPackageName, mPermName);
        } else {
            mStatus = Utils.getUIPermRuleStatus(mViewCtxStr, mViewInfoStr, mPermName);
        }
        return mStatus;
    }

    public void setStatus(boolean status) {
        if (mType == START_PERMRULE) {
            Utils.setStartPermRuleStatus(mPackageName, mPermName, status);
        } else {
            Utils.setUIPermRuleStatus(mViewCtxStr, mViewInfoStr, mPermName, status);
        }
    }
}
