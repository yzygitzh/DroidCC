package yzygitzh.droidcc;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ListView;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {
    private ListView mMainListView;
    private ArrayAdapter<String> mMainListAdaptor;
    private List<String> mMainListContents = new ArrayList<>();

    void initPackageList() {
        final Handler textHandler = new Handler();
        final Activity activityCtx = this;

        mMainListView = (ListView) findViewById(R.id.main_list_view);
        mMainListAdaptor = new ArrayAdapter<>(this, R.layout.list_item_main, R.id.list_content_main, mMainListContents);
        mMainListView.setAdapter(mMainListAdaptor);

        new Thread() {
            @Override
            public void run() {
                super.run();
                Utils.initUtils(activityCtx);

                mMainListContents.clear();
                for (String jsonFileName: Utils.getPermRules().keySet()) {
                    mMainListContents.add(jsonFileName);
                }

                textHandler.post(new Runnable() {
                    public void run() {
                        mMainListAdaptor.notifyDataSetChanged();
                        mMainListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                            @Override
                            public void onItemClick(AdapterView<?> adapter, View view, int position, long arg) {
                                Intent appInfo = new Intent(activityCtx, UIChooserActivity.class);
                                String jsonFileName = mMainListContents.get(position);
                                appInfo.putExtra("title", jsonFileName);
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
        setContentView(R.layout.activity_main);

        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        initPackageList();
        /*
        String testViewContextStr = "activity=com.devexpert.weather.view.HomeActivity;package=com.devexpert.weather;view_action_id=0";
        String testViewInfoStr = "thisRect=200 449 210 491;rootRect=0 0 768 1280;thisResId=com.devexpert.weather:id/text_mylocation_home;rootResId=";
        mDcm.setUIPermRule(testViewContextStr, testViewInfoStr, "android.permission.INTERNET", true);
        mDcm.setUIPermRule(testViewContextStr, testViewInfoStr, "android.permission.ACCESS_FINE_LOCATION", true);
        */
    }

}
