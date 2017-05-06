package yzygitzh.droidcc;

import android.app.Activity;
import android.app.DroidCCManager;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Environment;
import android.support.design.widget.Snackbar;
import android.view.View;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

/**
 * Created by yzy on 5/4/17.
 */

public class Utils {
    private static DroidCCManager mDcm;
    private static Map<String, JSONObject> mPermRules;

    public static final String UI_PERM_RULES = "ui_perm_rules";
    public static final String START_PERM_RULES = "start_perm_rules";
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
                retObj.put(permRuleFile.getName(), jsonObj);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        return retObj;
    }
}
