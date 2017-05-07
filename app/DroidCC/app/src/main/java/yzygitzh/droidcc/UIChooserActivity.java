package yzygitzh.droidcc;

import android.app.Activity;
import android.content.Intent;
import android.os.Handler;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ListView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class UIChooserActivity extends AppCompatActivity {
    private ListView mUIListView, mStartListView;
    private ArrayAdapter<String> mUIListAdaptor;
    private PermRuleAdaptor mStartListAdaptor;
    private List<String> mUIListContents = new ArrayList<>();
    private List<PermRuleContent> mStartListContents = new ArrayList<>();
    private String packageName;

    void initActivityList() {
        final Handler textHandler = new Handler();
        final Activity activityCtx = this;

        packageName = getIntent().getStringExtra(Utils.PACKAGE_NAME);
        setTitle(packageName);

        mUIListView = (ListView) findViewById(R.id.uichooser_ui_list_view);
        mStartListView = (ListView) findViewById(R.id.uichooser_start_list_view);

        mUIListAdaptor = new ArrayAdapter<>(this, R.layout.list_item_uichooser, R.id.list_content_uichooser, mUIListContents);
        mStartListAdaptor = new PermRuleAdaptor(this, mStartListContents);

        mUIListView.setAdapter(mUIListAdaptor);
        mStartListView.setAdapter(mStartListAdaptor);

        new Thread() {
            @Override
            public void run() {
                super.run();

                mUIListContents.clear();
                try {
                    JSONObject UIPermRules = (JSONObject) Utils.getPermRules().get(packageName).get(Utils.UI_PERM_RULES);
                    Iterator<String> keyItr = UIPermRules.keys();
                    while (keyItr.hasNext()) mUIListContents.add(keyItr.next());
                } catch (JSONException e) {
                    e.printStackTrace();
                }

                mStartListContents.clear();
                try {
                    JSONArray perms = (JSONArray) Utils.getPermRules().get(packageName).get(Utils.START_PERM_RULES);
                    for (int i = 0; i < perms.length(); i++) {
                        String permission = perms.getString(i);
                        boolean status = Utils.getStartPermRuleStatus(packageName, permission);
                        mStartListContents.add(new PermRuleContent(perms.getString(i), status));
                    }
                } catch (JSONException e) {
                    e.printStackTrace();
                }

                textHandler.post(new Runnable() {
                    public void run() {
                        mUIListAdaptor.notifyDataSetChanged();
                        mStartListAdaptor.notifyDataSetChanged();
                        mUIListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                            @Override
                            public void onItemClick(AdapterView<?> adapter, View view, int position, long arg) {
                                Intent appInfo = new Intent(activityCtx, PermRulesActivity.class);
                                String activityName = mUIListContents.get(position);
                                appInfo.putExtra(Utils.PACKAGE_NAME, packageName);
                                appInfo.putExtra(Utils.ACTIVITY_NAME, activityName);
                                startActivity(appInfo);
                            }
                        });
                    }
                });
            }
        }.start();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_uichooser);
        initActivityList();
    }
}
