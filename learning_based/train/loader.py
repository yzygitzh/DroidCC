#coding=utf-8

import logging
logging.basicConfig(format="%(asctime)-15s %(message)s")
import os
import pickle
import queue
import random
import threading
import time

import numpy as np
import tensorflow as tf

class Loader():
    """Basic data loader
    """
    def __init__(self, config_json):
        self.x_dim, self.y_dim = config_json["screen_res"]
        self.image_channels = config_json["image_channels"]
        self.total_perms = config_json["total_perms"]
        self.word_embedding_dim = config_json["word_embedding_dim"]
        self.training_data_dir = config_json["training_data_dir"]
        self.logger = logging.getLogger("loader")
        self.logger.setLevel(logging.INFO)

    def next_batch(self):
        pass

class SingleScreenLoader(Loader):
    """Normal single screen data loader, in contrast to debug data loader
    """
    def __init__(self, config_json):
        super().__init__(config_json)
        self.batch_size = config_json["batch_size"]
        self.data_buffer_size = config_json["data_buffer_size"]
        self.data_files = next(os.walk(self.training_data_dir))[2]
        # self.data_files = ["jp.naver.linecard.android.pickle",
        #                    "co.brainly.pickle"]
        self.data_paths = [os.path.join(self.training_data_dir, x) for x in self.data_files]
        self.data_queue = queue.Queue()
        self.path_queue = queue.Queue()
        self.epochs = -1
        self.loading_thread = None
        self.stopped = False

    def get_current_epoch(self):
        return self.epochs

    def reload_paths(self):
        self.epochs += 1
        self.logger.info("epoch: %d", self.epochs)
        random.shuffle(self.data_paths)
        for data_path in self.data_paths:
            self.path_queue.put(data_path)

    def load_pickles(self, data_paths):
        data_item_list = []
        for data_path in data_paths:
            with open(data_path, "rb") as f:
                input_data = pickle.load(f)
            for ui_event in input_data:
                data_item_list.append(ui_event)
        rand_idx = list(range(len(data_item_list)))
        random.shuffle(rand_idx)
        for i in rand_idx:
            self.data_queue.put(data_item_list[i])

    def next_batch_producer(self):
        # always try to load data when < threshold
        # poll check threshold
        while not self.stopped:
            if self.data_queue.qsize() < self.data_buffer_size:
                paths_to_load = []
                if self.path_queue.empty():
                    self.reload_paths()
                paths_to_load.append(self.path_queue.get())
                # self.logger.info("loading: %s", paths_to_load[-1])
                self.load_pickles(paths_to_load)
            time.sleep(0.05)

    def next_batch_consumer(self):
        # always try to get data
        batch_tuple = None
        for i in range(self.batch_size):
            data_item = self.data_queue.get()
            if batch_tuple is None:
                batch_tuple = tuple([] for _ in range(len(data_item)))
            for idx in range(len(batch_tuple)):
                batch_tuple[idx].append(data_item[idx])
        stacked_tuple = ()
        for idx in range(len(batch_tuple)):
            stacked_tuple += (np.stack(batch_tuple[idx]),)

        assert stacked_tuple[0].shape == (self.batch_size, self.x_dim, self.y_dim, self.image_channels), \
            "image dimension not correct: " + stacked_tuple[0].shape
        assert stacked_tuple[1].shape == (self.batch_size, self.word_embedding_dim), \
            "ui_text dimension not correct: " + stacked_tuple[1].shape
        assert stacked_tuple[2].shape == (self.batch_size, self.word_embedding_dim), \
            "ui_resource_id dimension not correct: " + stacked_tuple[2].shape
        assert stacked_tuple[3].shape == (self.batch_size, self.word_embedding_dim), \
            "elem_text dimension not correct: " + stacked_tuple[3].shape
        assert stacked_tuple[4].shape == (self.batch_size, self.word_embedding_dim), \
            "text_resource_id dimension not correct: " + stacked_tuple[4].shape
        assert stacked_tuple[5].shape == (self.batch_size, self.total_perms), \
            "perms dimension not correct: " + stacked_tuple[5].shape

        return stacked_tuple

    def next_batch(self):
        if self.loading_thread is None:
            self.loading_thread = threading.Thread(target=self.next_batch_producer)
            self.loading_thread.start()
        return self.next_batch_consumer()

    def stop(self):
        self.stopped = True
