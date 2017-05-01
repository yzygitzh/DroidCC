package yzygitzh.droidcc;

import android.app.DroidCCManager;
import android.os.Bundle;
import android.support.design.widget.FloatingActionButton;
import android.support.design.widget.Snackbar;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.View;

public class MainActivity extends AppCompatActivity {
    private static DroidCCManager dcm;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        dcm = (DroidCCManager) getSystemService("droid_cc");
        String testViewContextStr = "activity=com.devexpert.weather.view.HomeActivity;package=com.devexpert.weather;view_action_id=0";
        //String testViewInfoStr = "screenX=12;screenY=170;thisWidth=146;thisHeight=23;rootWidth=320;rootHeight=480;thisResId=com.devexpert.weather:id/text_weather_home;rootResId=";
        String testViewInfoStr = "thisRect=24 415 380 461;rootRect=0 0 768 1280;thisResId=com.devexpert.weather:id/text_weather_home;rootResId=";
        dcm.setUIPermRule(testViewContextStr, testViewInfoStr, "android.permission.INTERNET", true);
        dcm.setUIPermRule(testViewContextStr, testViewInfoStr, "android.permission.ACCESS_FINE_LOCATION", true);
        //dcm.setPermission(testViewContextStr, testViewInfoStr, "android.permission.INTERNET", false);

        FloatingActionButton fab = (FloatingActionButton) findViewById(R.id.fab);
        fab.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Snackbar.make(view, "Replace with your own action", Snackbar.LENGTH_LONG)
                        .setAction("Action", null).show();
            }
        });
    }

}
