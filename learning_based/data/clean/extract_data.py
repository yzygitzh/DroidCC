#coding=utf-8

import argparse
import json
import os
import pickle

import utils

def extract_data(config_path, input_dir):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    db_output = utils.DroidBotOutput(config_json, input_dir)
    ui_perm_list = db_output.get_ui_perm_list()

    pkg_name = db_output.get_pkg_name()
    output_dir = config_json["output_dir"]
    pickle_path = os.path.join(output_dir, "%s.pickle" % pkg_name)
    with open(pickle_path, "wb") as f:
        pickle.dump(ui_perm_list, f)

    print(pkg_name, len(ui_perm_list), "done")

def parse_args():
    parser = argparse.ArgumentParser(description="UI-code data cleaner")
    parser.add_argument("-c", action="store", dest="config_path",
                        required=True, help="path/to/config.json")
    parser.add_argument("-i", action="store", dest="input_dir",
                        required=True, help="path/to/droidbot_out")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    extract_data(opts.config_path, opts.input_dir)

if __name__ == "__main__":
    main()
