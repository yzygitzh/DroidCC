#coding=utf-8

import argparse
import json
import os

import utils

def run(config_path, input_dir):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)
    text_stat_dir = config_json["text_stat_dir"]

    assert os.path.exists(input_dir), "DroidBot folder doesn't exist"

    # find package name
    dumpsys_candidates = [x for x in next(os.walk(input_dir))[2]
                          if "dumpsys" in x]
    assert len(dumpsys_candidates) == 1, "dumpsys file doesn't exist"
    dumpsys_filename = dumpsys_candidates[0]
    pkg_name = dumpsys_filename.split("_")[-1][:-len(".txt")]

    # find text in state_json
    states_folder_path = os.path.join(input_dir, "states")
    assert os.path.exists(states_folder_path), "states folder doesn't exist"
    state_paths = [os.path.join(states_folder_path, x)
                   for x in next(os.walk(states_folder_path))[2]
                   if ".json" in x]
    word_set = set()
    tc = utils.TextCleaner()
    for state_path in state_paths:
        if os.stat(state_path).st_size != 0:
            with open(state_path, "r") as f:
                state_json = json.load(f)
                foreground_activity = state_json["foreground_activity"]
                if pkg_name in foreground_activity:
                    for view in state_json["views"]:
                        if "text" in view and view["text"] is not None:
                            word_set.update(tc.clean(view["text"]))
                        if "resource_id" in view and view["resource_id"] is not None:
                            resource_id = view["resource_id"]
                            if "/" in view["resource_id"]:
                                resource_id = resource_id.split("/")[1]
                            word_set.update(tc.clean(resource_id))

    output_path = os.path.join(text_stat_dir, "%s.txt" % pkg_name)
    with open(output_path, "w") as f:
        f.writelines([x + os.linesep for x in sorted(word_set)])

def parse_args():
    parser = argparse.ArgumentParser(description="Extract words appeared in DroidBot output")
    parser.add_argument("-c", action="store", dest="config_path",
                        required=True, help="path/to/config.json")
    parser.add_argument("-i", action="store", dest="input_dir",
                        required=True, help="path/to/droidbot_out")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    run(opts.config_path, opts.input_dir)

if __name__ == "__main__":
    main()
