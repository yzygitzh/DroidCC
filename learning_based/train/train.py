#coding=utf-8

import argparse
import json
import logging
logging.basicConfig(format="%(asctime)-15s %(message)s")
import os
import shutil

import numpy as np
import tensorflow as tf

import loader
import model

def run(config_path):
    with open(config_path, "r") as config_file:
        config_json = json.load(config_file)

    log_data_dir = config_json["log_data_dir"]
    shutil.rmtree(log_data_dir)
    os.makedirs(log_data_dir)

    learning_rate = config_json["learning_rate"]
    max_iter = config_json["max_iter"]
    log_step = config_json["log_step"]
    snapshot_step = config_json["snapshot_step"]

    data_loader = loader.SingleScreenLoader(config_json)
    screen_model = model.SingleScreenModel(config_json)
    merged_summary = tf.summary.merge_all()

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    logger = logging.getLogger("train")
    logger.setLevel(logging.INFO)

    saver = tf.train.Saver(max_to_keep=None)

    with tf.Session(config=tf_config) as sess:
        train_writer = tf.summary.FileWriter(log_data_dir, sess.graph)

        optimizer = tf.train.MomentumOptimizer(learning_rate, 0.9)
        trainer = optimizer.minimize(screen_model.total_loss)

        sess.run(tf.global_variables_initializer())
        for i in range(max_iter):
            feed_dict = screen_model.get_feed_dict(*data_loader.next_batch())
            sess.run(trainer, feed_dict=feed_dict)

            if i % snapshot_step == 0:
                saved_path = saver.save(sess, os.path.join(log_data_dir, "model_%d.ckpt" % i))
                logger.info("model saved in path: %s" % saved_path)

            if i % log_step == 0:
                summary = sess.run(merged_summary, feed_dict=feed_dict)
                train_writer.add_summary(summary, i)
                train_writer.flush()

    data_loader.stop()

def parse_args():
    parser = argparse.ArgumentParser(description="Humanoid training script")
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
