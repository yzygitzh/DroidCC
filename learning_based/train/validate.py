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

    threshold_path = config_json["threshold_path"]
    with open(threshold_path, "r") as threshold_file:
        threshold_json = json.load(threshold_file)

    config_json["training_data_dir"] = config_json["validation_data_dir"]
    total_perms = config_json["total_perms"]
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

    sample_num = 0
    true_sample_num = [0] * total_perms
    false_sample_num = [0] * total_perms
    false_reject = [0] * total_perms
    false_accept = [0] * total_perms
    correct_reject = [0] * total_perms
    correct_accept = [0] * total_perms

    while data_loader.get_current_epoch() < 1:
        feed_dict = screen_model.get_feed_dict(*data_loader.next_batch())
        true_perms, predict_perms, loss, input_images = \
            sess.run([screen_model.true_perms,
                      screen_model.fc,
                      screen_model.perm_loss,
                      screen_model.input_images], feed_dict=feed_dict)
        for i in range(total_perms):
            ground_truth = 0
            if true_perms[0][i] > 1e-6:
                ground_truth = 1
                true_sample_num[i] += 1
            else:
                false_sample_num[i] += 1
            lower_bound = threshold_json[i]["lower_bound"]
            if lower_bound is None:
                lower_bound = 2.0
            upper_bound = threshold_json[i]["upper_bound"]
            if upper_bound is None:
                upper_bound = -1.0
            if lower_bound > upper_bound:
                upper_bound = lower_bound
            if predict_perms[0][i] < lower_bound:
                if ground_truth == 1:
                    false_reject[i] += 1
                else:
                    correct_reject[i] += 1
            if predict_perms[0][i] > upper_bound:
                if ground_truth == 0:
                    false_accept[i] += 1
                else:
                    correct_accept[i] += 1

        # print(loss)
        # plt.imshow(input_images.reshape((x_dim, y_dim, image_channels)), interpolation='nearest')
        # plt.show()
        sample_num += 1
        if sample_num % 1000 == 0:
            print(sample_num)
    data_loader.stop()

    # for each permission, output validation result
    print("sample_num", sample_num)
    total_false_rejects = 0
    total_false_accepts = 0
    total_true_samples = 0
    total_false_samples = 0
    total_excluded_rate = 0
    for i in range(total_perms):
        if i not in [2, 3, 5, 23, 24]:
            continue
        total_false_rejects += false_reject[i]
        total_false_accepts += false_accept[i]
        total_true_samples += true_sample_num[i]
        total_false_samples += false_sample_num[i]
        print(i)
        print("true_sample_num", true_sample_num[i])
        print("false_reject_rate", false_reject[i] / true_sample_num[i] \
              if true_sample_num[i] > 0 else 0.0)
        print("false_accept_rate", false_accept[i] / false_sample_num[i] \
              if false_sample_num[i] > 0 else 0.0)
        print("correct_reject_rate", correct_reject[i] / false_sample_num[i] \
              if false_sample_num[i] > 0 else 0.0)
        print("correct_accept_rate", correct_accept[i] / true_sample_num[i] \
              if true_sample_num[i] > 0 else 0.0)
        excluded_rate = (correct_reject[i] + correct_accept[i]) / sample_num
        print("exclude_rate", excluded_rate if sample_num > 0 else 0.0)
        total_excluded_rate += excluded_rate / total_perms
    print("total_false_reject_rate", total_false_rejects / total_true_samples)
    print("total_false_accept_rate", total_false_accepts / total_false_samples)
    print("total_excluded_rate", total_excluded_rate)

def parse_args():
    parser = argparse.ArgumentParser(description="DroidCC validating script")
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
