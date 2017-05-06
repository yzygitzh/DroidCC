package android.app;

import java.util.List;

public class DroidCCManager {
    public void setViewTouch(List<String> idxList, List<String> viewStrList) {
        return;
    }

    public void setViewBack(List<String> idxList, List<String> viewStrList) {
        return;
    }

    public boolean checkPermission(String permission, int uid){
        return true;
    }

    public void clearView(int uid, int pid) {
        return;
    }

    public void setUIPermRule(String viewContextStr, String viewInfoStr, String permission, boolean status) {
        return;
    }

    public boolean getUIPermRuleStatus(String viewContextStr, String viewInfoStr, String permission) {
        return true;
    }

    public void setStartPermRule(String packageName, String permission, boolean status) {
        return;
    }

    public boolean getStartPermRuleStatus(String packageName, String permission) {
        return true;
    }
}