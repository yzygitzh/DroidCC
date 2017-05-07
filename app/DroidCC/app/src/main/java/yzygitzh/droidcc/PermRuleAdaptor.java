package yzygitzh.droidcc;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Switch;
import android.widget.TextView;

import java.util.List;

/**
 * Created by yzy on 5/6/17.
 */

public class PermRuleAdaptor extends BaseAdapter {
    private LayoutInflater mInflater;
    private List<PermRuleContent> mContents;

    public PermRuleAdaptor(Context ctx, List<PermRuleContent> contents) {
        mInflater = LayoutInflater.from(ctx);
        mContents = contents;
    }

    @Override
    public int getCount() {
        return mContents.size();
    }

    @Override
    public Object getItem(int idx) {
        return mContents.get(idx);
    }

    @Override
    public long getItemId(int position) {
        return mContents.indexOf(getItem(position));
    }

    private class ViewHolder {
        TextView mTextView;
        Switch mSwitchView;
        public ViewHolder(TextView textView, Switch switchView){
            mTextView = textView;
            mSwitchView = switchView;
        }
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        ViewHolder holder = null;
        if (convertView==null) {
            convertView = mInflater.inflate(R.layout.list_item_permrules, null);
            holder = new ViewHolder(
                    (TextView) convertView.findViewById(R.id.list_content_permrule_text),
                    (Switch) convertView.findViewById(R.id.list_content_permrule_switch)
            );
            convertView.setTag(holder);
        } else {
            holder = (ViewHolder) convertView.getTag();
        }
        PermRuleContent content = (PermRuleContent) getItem(position);
        holder.mTextView.setText(content.getPermName());
        holder.mSwitchView.setChecked(content.getStatus());
        return convertView;
    }
}
