#coding=utf-8

import argparse
import json

def run(input_dir, config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)
    config_json["input_dir"] = input_dir

def parse_args():
    parser = argparse.ArgumentParser(description="UI-code data cleaner")
    parser.add_argument("-i", action="store", dest="input_dir",
                        required=True, help="path/to/droidbot_out")
    parser.add_argument("-c", action="store", dest="config_path",
                        required=True, help="path/to/config.json")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    run(opts.input_dir, opts.config_path)

if __name__ == "__main__":
    main()