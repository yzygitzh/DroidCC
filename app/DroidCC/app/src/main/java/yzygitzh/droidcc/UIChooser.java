package yzygitzh.droidcc;

import android.content.Intent;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;

public class UIChooser extends AppCompatActivity {

    void initActivityList() {
        Intent intent = getIntent();
        String title = intent.getStringExtra("title");
        setTitle(title);

        String jsonStr = intent.getStringExtra("packageData");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_uichooser);
        initActivityList();
    }
}
