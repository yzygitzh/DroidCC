#coding=utf-8

import argparse
import json
import logging
logging.basicConfig(format="%(asctime)-15s %(message)s")
import os

import numpy as np
import tensorflow as tf

import loader
import model

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    config_json["training_data_dir"] = config_json["validation_data_dir"]
    config_json["data_threads"] = 1
    config_json["data_buffer_size"] = 10
    config_json["weight_decay"] = 0.0
    config_json["batch_size"] = 1

    data_loader = loader.SingleScreenLoader(config_json)
    screen_model = model.SingleScreenModel(config_json)

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    logger = logging.getLogger("train")
    logger.setLevel(logging.INFO)

    saver = tf.train.Saver()
    sess = tf.Session()
    saver.restore(sess, config_json["model_path"])

    while data_loader.get_current_epoch() < 1:
        feed_dict = screen_model.get_feed_dict(*data_loader.next_batch())
        true_perms, predict_perms, loss = sess.run([screen_model.true_perms,
                                                    screen_model.fc,
                                                    screen_model.perm_loss], feed_dict=feed_dict)
        print(true_perms)
        print(predict_perms)
        print(loss)
        break

    data_loader.stop()

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
