package yzygitzh.droidcc;

import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Handler;
import android.support.v4.app.FragmentStatePagerAdapter;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;

import android.support.v4.app.Fragment;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.FragmentPagerAdapter;
import android.support.v4.view.ViewPager;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;

public class PermRulesActivity extends AppCompatActivity {
    private SectionsPagerAdapter mSectionsPagerAdapter;

    private ViewPager mViewPager;
    private String mTitle;

    void initPermRulesList() {
        mTitle = getIntent().getStringExtra(Utils.ACTIVITY_NAME);
        setTitle(mTitle);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_perm_rules);

        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        mSectionsPagerAdapter = new SectionsPagerAdapter(getSupportFragmentManager());

        mViewPager = (ViewPager) findViewById(R.id.container);
        mViewPager.setAdapter(mSectionsPagerAdapter);

        initPermRulesList();
    }

    public static class PlaceholderFragment extends Fragment {
        private static final String SECTION_NUMBER = "section_number";
        private static final String TOTAL_SECTION_NUMBER = "total_section_number";

        private TextView mTextView;

        private ImageView mImageView;

        private ListView mListView;
        private ArrayAdapter<String> mListAdaptor;
        private List<String> mListContents = new ArrayList<>();

        public PlaceholderFragment() {
        }

        /**
         * Returns a new instance of this fragment for the given section
         * number.
         */
        public static PlaceholderFragment newInstance(int sectionNumber, int totalSectionNumber, String packageName, String activityName) {
            PlaceholderFragment fragment = new PlaceholderFragment();
            Bundle args = new Bundle();
            args.putInt(SECTION_NUMBER, sectionNumber);
            args.putInt(TOTAL_SECTION_NUMBER, totalSectionNumber);
            args.putString(Utils.PACKAGE_NAME, packageName);
            args.putString(Utils.ACTIVITY_NAME, activityName);
            fragment.setArguments(args);
            return fragment;
        }

        @Override
        public View onCreateView(LayoutInflater inflater, ViewGroup container,
                                 Bundle savedInstanceState) {
            final Handler textHandler = new Handler();

            View rootView = inflater.inflate(R.layout.content_perm_rules, container, false);

            mTextView = (TextView) rootView.findViewById(R.id.permrules_text_view);

            mImageView = (ImageView) rootView.findViewById(R.id.permrules_image_view);

            mListView = (ListView) rootView.findViewById(R.id.permrules_list_view);
            mListContents = new ArrayList<>();
            mListAdaptor = new ArrayAdapter<>(getActivity(),
                    R.layout.list_item_permrules, R.id.list_content_permrules, mListContents);
            mListView.setAdapter(mListAdaptor);

            new Thread() {
                @Override
                public void run() {
                    super.run();
                    mListContents.clear();
                    try {
                        JSONObject UIPermRules = ((JSONObject) Utils.getPermRules()
                                .get(getArguments().getString(Utils.PACKAGE_NAME))
                                .get(Utils.UI_PERM_RULES))
                                .getJSONArray(getArguments().getString(Utils.ACTIVITY_NAME))
                                .getJSONObject(getArguments().getInt(SECTION_NUMBER));

                        JSONArray perms = UIPermRules.getJSONArray("permission");
                        for (int i = 0; i < perms.length(); i++)
                            mListContents.add(perms.getString(i));

                        final StringBuilder description = new StringBuilder();
                        description.append(String.format("Event Type: %s%n", UIPermRules.getString(Utils.EVENT_TYPE)));
                        description.append(String.format("Tag: %s%n", UIPermRules.getString(Utils.EVENT_TAG)));
                        JSONArray bounds = UIPermRules.getJSONArray(Utils.EVENT_BOUNDS);
                        description.append(String.format("Bounds: %d, %d, %d, %d%n",
                                ((JSONArray)bounds.get(0)).getInt(0),
                                ((JSONArray)bounds.get(0)).getInt(1),
                                ((JSONArray)bounds.get(1)).getInt(0),
                                ((JSONArray)bounds.get(1)).getInt(1)));
                        description.append(String.format("Rules: %d / %d",
                                getArguments().getInt(SECTION_NUMBER) + 1, getArguments().getInt(TOTAL_SECTION_NUMBER)));

                        final Bitmap screenshot = Utils.getImage(UIPermRules.getString(Utils.EVENT_TAG), getActivity());

                        textHandler.post(new Runnable() {
                            public void run() {
                                mListAdaptor.notifyDataSetChanged();
                                mTextView.setText(description);
                                mImageView.setImageBitmap(screenshot);
                            }
                        });
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }

                }
            }.start();

            return rootView;
        }
    }

    public class SectionsPagerAdapter extends FragmentStatePagerAdapter {

        public SectionsPagerAdapter(FragmentManager fm) {
            super(fm);
        }

        @Override
        public Fragment getItem(int position) {
            return PlaceholderFragment.newInstance(position, getCount(),
                    getIntent().getStringExtra(Utils.PACKAGE_NAME),
                    getIntent().getStringExtra(Utils.ACTIVITY_NAME));
        }

        @Override
        public int getCount() {
            try {
                return ((JSONObject) Utils.getPermRules()
                        .get(getIntent().getStringExtra(Utils.PACKAGE_NAME))
                        .get(Utils.UI_PERM_RULES))
                        .getJSONArray(getIntent().getStringExtra(Utils.ACTIVITY_NAME)).length();
            } catch (JSONException e) {
                e.printStackTrace();
            }
            return 0;
        }
    }
}
