package yzygitzh.droidcc;

import android.app.Activity;
import android.app.DroidCCManager;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Environment;
import android.support.design.widget.Snackbar;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Switch;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Created by yzy on 5/4/17.
 */

public class Utils {
    private static DroidCCManager mDcm;
    private static Map<String, JSONObject> mPermRules;

    public static int APP_PERM_GRANTED = 0;
    public static final String UI_PERM_RULES = "ui_perm_rules";
    public static final String START_PERM_RULES = "start_perm_rules";
    public static final String VIEW_PERM_KEY = "permission";
    public static final String PERM_RULES_KEY = "perm";
    public static final String PACKAGE_NAME = "packageName";
    public static final String ACTIVITY_NAME = "activityName";
    public static final String EVENT_TYPE = "eventType";
    public static final String EVENT_TAG = "eventTag";
    public static final String EVENT_BOUNDS = "bounds";
    public static final String EVENT_VIEWCTXSTR = "viewCtxStr";
    public static final String EVENT_VIEWINFOSTR = "viewInfoStr";


    public static boolean initUtils(Activity activityCtx) {
        if (mDcm == null ) mDcm = Utils.initDroidCC(activityCtx);
        if (mDcm == null) return false;
        if (mPermRules == null) mPermRules = Utils.initPermRules(activityCtx);
        if (mPermRules == null) return false;

        /*
        String testViewContextStr = "activity=com.devexpert.weather.view.HomeActivity;package=com.devexpert.weather;view_action_id=0";
        String testViewInfoStr = "thisRect=200 449 210 491;rootRect=0 0 768 1280;thisResId=com.devexpert.weather:id/text_mylocation_home;rootResId=";

        mDcm.setUIPermRule(testViewContextStr, testViewInfoStr, "android.permission.INTERNET", true);
        mDcm.setStartPermRule("com.devexpert.weather", "android.permission.INTERNET", false);

        boolean UIResult = mDcm.getUIPermRuleStatus(testViewContextStr, testViewInfoStr, "android.permission.INTERNET");
        Log.d("DroidCCUtils: UI", Boolean.toString(UIResult));
        boolean startResult = mDcm.getStartPermRuleStatus("com.devexpert.weather", "android.permission.INTERNET");
        Log.d("DroidCCUtils: Start", Boolean.toString(startResult));
        */

        return true;
    }

    public static Map<String, JSONObject> getPermRules() {
        return mPermRules;
    }

    public static Bitmap getImage(String imageTag, Activity activityCtx) {
        File sdcardPath = Environment.getExternalStorageDirectory();
        File screenShotDir = new File(sdcardPath.getAbsolutePath(), activityCtx.getResources().getString(R.string.droidcc_screenshot_path));
        File imageFile = new File(screenShotDir, String.format("%s.png", imageTag));
        if(imageFile.exists()){
            return BitmapFactory.decodeFile(imageFile.getAbsolutePath());
        }
        return null;
    }

    public static boolean getStartPermRuleStatus(String packageName, String permission) {
        if (mDcm == null) return false;
        return mDcm.getStartPermRuleStatus(packageName, permission);
    }

    public static void setStartPermRuleStatus(String packageName, String permission, boolean status) {
        if (mDcm == null) return;
        mDcm.setStartPermRule(packageName, permission, status);
    }

    public static boolean getUIPermRuleStatus(String viewCtxStr, String viewInfoStr, String permission) {
        if (mDcm == null) return false;
        return mDcm.getUIPermRuleStatus(viewCtxStr, viewInfoStr, permission);
    }

    public static void setUIPermRuleStatus(String viewCtxStr, String viewInfoStr, String permission, boolean status) {
        if (mDcm == null) return;
        mDcm.setUIPermRule(viewCtxStr, viewInfoStr, permission, status);
    }

    private static void showMsg(View targetView, int strId) {
        Snackbar.make(targetView, strId, Snackbar.LENGTH_SHORT).show();
    }

    private static DroidCCManager initDroidCC(Activity activityCtx) {
        DroidCCManager dcm = (DroidCCManager) activityCtx.getSystemService(activityCtx.getResources().getString(R.string.droidcc_service_name));
        if (dcm == null) Utils.showMsg(activityCtx.findViewById(R.id.main_activity_layout), R.string.droidcc_service_fail);
        else Utils.showMsg(activityCtx.findViewById(R.id.main_activity_layout), R.string.droidcc_service_success);
        return dcm;
    }

    private static Map<String, JSONObject> initPermRules(Activity activityCtx) {
        Map<String, JSONObject> retObj = new HashMap<>();

        File sdcardPath = Environment.getExternalStorageDirectory();
        File permRuleDir = new File(sdcardPath.getAbsolutePath(), activityCtx.getResources().getString(R.string.droidcc_permrules_path));

        File[] permRuleFiles = permRuleDir.listFiles();
        StringBuilder permRuleFileListStr = new StringBuilder();

        for (File permRuleFile: permRuleFiles) {
            try {
                FileInputStream fs = new FileInputStream(permRuleFile);
                FileChannel fc = fs.getChannel();
                MappedByteBuffer bb = fc.map(FileChannel.MapMode.READ_ONLY, 0, fc.size());
                String jsonStr = Charset.defaultCharset().decode(bb).toString();

                JSONObject jsonObj = new JSONObject(jsonStr);
                String permRuleFileName = permRuleFile.getName();
                String packageName = permRuleFileName.substring(0, permRuleFileName.length() - ".json".length());
                retObj.put(packageName, jsonObj);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        return retObj;
    }
}
