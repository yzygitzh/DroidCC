#coding=utf-8

import argparse
import json
import os
import pickle

import utils

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)
    output_dir = config_json["output_dir"]

    # load sdk_map and cp_map, and generate total perm list
    sdk_map = utils.SDKMap(config_json).get_mapping()
    cp_map = utils.CPMap(config_json).get_mapping()
    perm_set = set()
    for perm_list in sdk_map.values():
        perm_set.update(perm_list)
    for uri, method, perm_list in cp_map:
        perm_set.update(perm_list)
    perm_list = sorted(perm_set)

    assert os.path.exists(output_dir), "training_data folder doesn't exist"

    data_paths = [os.path.join(output_dir, x)
                  for x in next(os.walk(output_dir))[2]]

    perm_count = {x: 0 for x in perm_list}
    data_count = 0
    for data_path in data_paths:
        with open(data_path, "rb") as f:
            data_items = pickle.load(f)
            for data_item in data_items:
                perm_onehot = data_item[-1]
                for idx, mark in enumerate(perm_onehot):
                    if perm_onehot[idx] > 1e-6:
                        perm_count[perm_list[idx]] += 1
                data_count += 1
                if data_count % 1000 == 0:
                    print(data_count)
    print("data_count:", data_count)
    print(json.dumps(perm_count, indent=2))

def parse_args():
    parser = argparse.ArgumentParser(description="Stat permissions triggered in training data")
    parser.add_argument("-c", action="store", dest="config_path",
                        required=True, help="path/to/config.json")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    run(opts.config_path)

if __name__ == "__main__":
    main()
