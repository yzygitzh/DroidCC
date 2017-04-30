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
        String testViewKeyStr = "activity=A;package=P;idx_list_join=I;view_action_id=1";
        dcm.setPermission(testViewKeyStr, "TEST_PERMISSION", true);
        dcm.setPermission(testViewKeyStr, "TEST_PERMISSION", false);

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
