#coding=utf-8

import argparse
import json
import logging
logging.basicConfig(format="%(asctime)-15s %(message)s")
import os

import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt

import loader
import model

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    total_perms = config_json["total_perms"]
    threshold_path = config_json["threshold_path"]
    config_json["data_threads"] = 1
    config_json["data_buffer_size"] = 10
    config_json["weight_decay"] = 0.0
    config_json["batch_size"] = 1
    x_dim, y_dim = config_json["screen_res"]
    image_channels = config_json["image_channels"]

    data_loader = loader.SingleScreenLoader(config_json)
    screen_model = model.SingleScreenModel(config_json)

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    logger = logging.getLogger("train")
    logger.setLevel(logging.INFO)

    saver = tf.train.Saver()
    sess = tf.Session()
    saver.restore(sess, config_json["model_path"])

    true_sensitivity_list = [[] for _ in range(total_perms)]
    false_sensitivity_list = [[] for _ in range(total_perms)]
    data_count = 0
    while data_loader.get_current_epoch() < 1:
        feed_dict = screen_model.get_feed_dict(*data_loader.next_batch())
        true_perms, predict_perms = sess.run([screen_model.true_perms,
                                              screen_model.fc], feed_dict=feed_dict)
        for i in range(total_perms):
            if true_perms[0][i] > 1e-6:
                true_sensitivity_list[i].append(predict_perms[0][i])
            else:
                false_sensitivity_list[i].append(predict_perms[0][i])
        data_count += 1
        if data_count % 1000 == 0:
            print(data_count)

    threshold_list = [{"lower_bound": None, "upper_bound": None}
                      for _ in range(total_perms)]
    for i in range(total_perms):
        sorted_true_sensitivities = sorted(true_sensitivity_list[i])
        sorted_false_sensitivities = sorted(false_sensitivity_list[i])
        if len(sorted_true_sensitivities) != 0:
            if len(sorted_true_sensitivities) < 100:
                threshold_list[i]["lower_bound"] = float(sorted_true_sensitivities[0])
            else:
                threshold_list[i]["lower_bound"] = \
                    float(sorted_true_sensitivities[int(len(sorted_true_sensitivities) * 0.01)])
        if len(sorted_false_sensitivities) != 0:
            if len(sorted_false_sensitivities) < 100:
                threshold_list[i]["upper_bound"] = float(sorted_false_sensitivities[0])
            else:
                threshold_list[i]["upper_bound"] = \
                    float(sorted_false_sensitivities[int(len(sorted_false_sensitivities) * 0.99)])

    data_loader.stop()
    with open(threshold_path, "w") as f:
        json.dump(threshold_list, f, indent=2)

def parse_args():
    parser = argparse.ArgumentParser(description="DroidCC model threshold picker")
    parser.add_argument("-c", action="store", dest="config_path",
                        required=True, help="path/to/config.json")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    run(opts.config_path)
    return

if __name__ == "__main__":
    main()
