#coding=utf-8

import argparse
import json
import os
import pickle

import utils
from matplotlib import pyplot as plt

def run(input_path):
    with open(input_path, "rb") as data_file:
        data_items = pickle.load(data_file)
        for data_item in data_items:
            print(data_item[-1])
            plt.imshow(data_item[0], interpolation='nearest')
            plt.show()

def parse_args():
    parser = argparse.ArgumentParser(description="Data visualizer")
    parser.add_argument("-i", action="store", dest="input_path",
                        required=True, help="path/to/droidbot_out")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    run(opts.input_path)

if __name__ == "__main__":
    main()
