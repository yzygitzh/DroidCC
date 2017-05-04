package yzygitzh.droidcc;

import android.app.Activity;
import android.app.DroidCCManager;
import android.content.Context;
import android.os.Environment;
import android.support.design.widget.Snackbar;
import android.view.View;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/**
 * Created by yzy on 5/4/17.
 */

public class Utils {
    public static void showMsg(View targetView, int strId) {
        Snackbar.make(targetView, strId, Snackbar.LENGTH_SHORT).show();
    }

    public static DroidCCManager initDroidCC(Activity activityCtx) {
        DroidCCManager dcm = (DroidCCManager) activityCtx.getSystemService("droid_cc");
        if (dcm == null) {
            Utils.showMsg(activityCtx.findViewById(R.id.main_activity_layout), R.string.droidcc_service_fail);
        } else {
            Utils.showMsg(activityCtx.findViewById(R.id.main_activity_layout), R.string.droidcc_service_success);
        }
        return dcm;
    }

    public static Map<String, JSONObject> initPermRules(Activity activityCtx) {
        Map<String, JSONObject> retObj = new HashMap<>();

        File sdcardPath = Environment.getExternalStorageDirectory();
        File permRuleDir = new File(sdcardPath.getAbsolutePath(), activityCtx.getResources().getString(R.string.droidcc_permrules_path));
        File screenShotDir = new File(sdcardPath.getAbsolutePath(), activityCtx.getResources().getString(R.string.droidcc_screenshot_path));

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
