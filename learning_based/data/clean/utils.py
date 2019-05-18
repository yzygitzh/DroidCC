#coding=utf-8

import datetime
import json
import numpy as np
import os
import re
import traceback

from matplotlib import pyplot as plt

class LogCat(object):
    """
    This class parses logcat file saved by DroidBot into
    (ts, query/update/insert/delete, uri)
    ts is in the format of DroidBot time tag
    """
    def __init__(self, config_json, logcat_path, pkg_name):
        self.timezone_diff = config_json["timezone_diff"]
        self.cp_access_list = None
        with open(logcat_path, "r") as f:
            self.cp_access_list = []
            logcat_lines = f.readlines()
            for line in logcat_lines:
                line_fields = line.strip().split()
                method = line_fields[6][:-1]
                if method in ["query", "update", "insert", "delete"]:
                    logcat_pkg_name = line_fields[7]
                    uri = line_fields[8]
                    if logcat_pkg_name == pkg_name:
                        ts_str = "2019-" + line_fields[0] + " " + line_fields[1].split(".")[0]
                        ts = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        ts += datetime.timedelta(hours=self.timezone_diff)
                        ts_str = ts.strftime("%Y-%m-%d_%H%M%S")
                        self.cp_access_list.append((ts_str, method, uri))

    def get_list(self):
        return self.cp_access_list

class SDKMap(object):
    """
    This class describes sdk"s method-permission mapping from axplorer
    """
    def __init__(self, config_json):
        self.mapping = None
        sdk_map_path = config_json["sdk_map_path"]
        with open(sdk_map_path, "r") as f:
            self.mapping = {}
            sdk_map_lines = f.readlines()
            for line in sdk_map_lines:
                line = line.strip()
                method = line.split("(")[0]
                perm_list = line.split("  ::  ")[1].split(", ")
                self.mapping[method] = perm_list

    def get_mapping(self):
        """
        :return: {method_name: permission_list}
        """
        return self.mapping

class CPMap(object):
    """
    This class describes content provider"s query-permission mapping from axplorer
    """
    def __init__(self, config_json):
        self.mapping = None
        cp_map_path = config_json["cp_map_path"]
        with open(cp_map_path, "r") as f:
            self.mapping = []
            sdk_map_lines = f.readlines()
            for line in sdk_map_lines:
                line = line.strip()
                line_fields = line.split("  ")
                permission = line_fields[-1]
                if permission == "[grant-uri-permission]":
                    continue
                uri_idx = 1
                uri = line_fields[uri_idx]
                uri_idx += 1
                if (line_fields[uri_idx].startswith("<path")):
                    uri += line_fields[uri_idx].split(":")[1][:-1]
                    # get rid of redundant slash
                    if uri[-1] == '/':
                        uri = uri[:-1]
                    uri_idx += 1
                if "R" in line_fields[-2]:
                    self.mapping.append((re.compile(uri + "(/[^/]+)*"), "query", [permission]))
                if "W" in line_fields[-2]:
                    self.mapping.append((re.compile(uri + "(/[^/]+)*"), "insert", [permission]))
                    self.mapping.append((re.compile(uri + "(/[^/]+)*"), "update", [permission]))
                    self.mapping.append((re.compile(uri + "(/[^/]+)*"), "delete", [permission]))

    def get_mapping(self):
        """
        :return: [(uri_pattern_regex, query/insert/update/delete, permission_list)]
        """
        return self.mapping

class UIEvent(object):
    """
    This class describes a UI transition event
    """

    def __init__(self, config_json,
                 state_path, event_path, trace_path, logcat,
                 sdk_map, cp_map, word_embedding):
        """
        Load screenshot, state json, event json and event method trace
        :param config_json: loaded JSON object of config file
        :param state_path: path to droidbot beginning state json
        :param event_path: path to droidbot event json
        :param trace_path: path to droidbot trace file
        :param logcat: logcat entries filtered by timestamp
        """

        self.screen_res = config_json["screen_res"]
        self.down_ratio = config_json["down_ratio"]
        self.text_dim = config_json["text_dim"]
        self.image_dim = config_json["image_dim"]
        self.interact_dim = config_json["interact_dim"]
        self.total_dims = config_json["total_dims"]
        self.back_view = config_json["back_view"]
        self.word_embedding_dim = config_json["word_embedding_dim"]

        self.state_path = state_path
        self.event_path = event_path
        self.trace_path = trace_path

        self.logcat = logcat

        self.sdk_map = sdk_map
        self.cp_map = cp_map
        self.word_embedding = word_embedding
        self.text_cleaner = TextCleaner()

        self.state = None
        with open(self.state_path, "r") as f:
            self.state = json.load(f)

        self.event = None
        with open(self.event_path, "r") as f:
            self.event = json.load(f)

        self.trace = None
        with open(self.trace_path, "r") as f:
            self.trace = f.readlines()

        # 1. process image
        self.down_dim = [int(self.screen_res[0] * self.down_ratio),
                         int(self.screen_res[1] * self.down_ratio)]
        self.image_data = np.zeros((self.down_dim[0], self.down_dim[1], self.total_dims),
                                   dtype=np.float32)

        # traverse state view hierarchy
        # generate ui text and resource_id embedding
        self.ui_text_embedding = []
        self.ui_resource_id_embedding = []

        for view in self.state["views"]:
            if len(view["children"]) == 0:
                draw_dim = self.text_dim if self.__is_text_view(view) else self.image_dim
                self.__color_view(view, draw_dim)
                text_embeddings, resource_id_embeddings = self.__process_view_text(view)
                self.ui_text_embedding += text_embeddings
                self.ui_resource_id_embedding += resource_id_embeddings

        self.ui_text_embedding = np.average(self.ui_text_embedding, axis=0) \
                                 if len(self.ui_text_embedding) > 0 \
                                 else np.zeros(self.word_embedding_dim)
        self.ui_resource_id_embedding = np.average(self.ui_resource_id_embedding, axis=0) \
                                        if len(self.ui_resource_id_embedding) > 0 \
                                        else np.zeros(self.word_embedding_dim)

        # color the interacted element
        # generate element text and resource_id embedding
        self.elem_text_embedding = []
        self.elem_resource_id_embedding = []

        if "view" in self.event["event"]:
            self.__color_view(self.event["event"]["view"], self.interact_dim)
            self.elem_text_embedding, self.elem_resource_id_embeddings = \
                self.__process_view_text(self.event["event"]["view"])
        elif self.event["event"]["event_type"] == "key" and \
             self.event["event"]["name"] == "BACK":
            self.__color_view(self.back_view, self.interact_dim)

        self.elem_text_embedding = np.average(self.elem_text_embedding, axis=0) \
                                   if len(self.elem_text_embedding) > 0 \
                                   else np.zeros(self.word_embedding_dim)
        self.elem_resource_id_embedding = np.average(self.elem_resource_id_embedding, axis=0) \
                                          if len(self.elem_resource_id_embedding) > 0 \
                                          else np.zeros(self.word_embedding_dim)

        assert self.ui_text_embedding.shape == (self.word_embedding_dim,), "embedding shape error"
        assert self.ui_resource_id_embedding.shape == (self.word_embedding_dim,), "embedding shape error"
        assert self.elem_text_embedding.shape == (self.word_embedding_dim,), "embedding shape error"
        assert self.elem_resource_id_embedding.shape == (self.word_embedding_dim,), "embedding shape error"

        # 2. process trace
        trace_idx = 0
        # find *method"
        while self.trace[trace_idx].strip() != "*methods":
            trace_idx += 1
        trace_idx += 1
        self.trace_methods = []
        while self.trace[trace_idx].strip() != "*end":
            trace_entry_fields = self.trace[trace_idx].split()
            self.trace_methods.append(trace_entry_fields[1] + "." + trace_entry_fields[2])
            trace_idx += 1

        self.perm_set = set()
        # 3. convert trace to permissions
        for method in self.trace_methods:
            if method in self.sdk_map:
                self.perm_set.update(self.sdk_map[method])

        # 4. convert logcat to permissions
        # (ts, query/update/insert/delete, uri)
        for ts, method, uri in self.logcat:
            # match uri for each cp_regex in cp map
            for cp_regex, cp_method, cp_perm_list in self.cp_map:
                if cp_regex.fullmatch(uri) is not None and cp_method == method:
                    self.perm_set.update(cp_perm_list)

    def __process_view_text(self, view):
        text_embeddings = []
        resource_id_embeddings = []
        if "text" in view and view["text"] is not None:
            word_list = self.text_cleaner.clean(view["text"])
            for word in word_list:
                if word in self.word_embedding:
                    # print(word, self.word_embedding[word])
                    text_embeddings.append(self.word_embedding[word])
        if "resource_id" in view and view["resource_id"] is not None:
            resource_id = view["resource_id"]
            # print(resource_id)
            if "/" in view["resource_id"]:
                resource_id = resource_id.split("/")[1]
            word_list = self.text_cleaner.clean(resource_id)
            # print(word_list)
            for word in word_list:
                if word in self.word_embedding:
                    # print(word, self.word_embedding[word])
                    resource_id_embeddings.append(self.word_embedding[word])
        return text_embeddings, resource_id_embeddings

    def __color_view(self, view, draw_dim):
        """
        Color the view in self.image_data given the dimension to color.
        """
        # draw view
        bounds = view["bounds"]
        x_min = int(bounds[0][0] * self.down_ratio)
        y_min = int(bounds[0][1] * self.down_ratio)
        x_max = int(bounds[1][0] * self.down_ratio)
        y_max = int(bounds[1][1] * self.down_ratio)
        if x_min >= x_max or y_min >= y_max:
            return
        self.image_data[x_min:x_max, y_min:y_max, draw_dim] = 1.0
        # draw view's four boundaries
        self.image_data[x_min - 1:x_min, y_min - 1:y_max + 1, draw_dim] = 0.0
        self.image_data[x_max:x_max + 1, y_min - 1:y_max + 1, draw_dim] = 0.0
        self.image_data[x_min - 1:x_max + 1, y_min - 1:y_min, draw_dim] = 0.0
        self.image_data[x_min - 1:x_max + 1, y_max:y_max + 1, draw_dim] = 0.0

    def __is_text_view(self, view):
        return "text" in view and view["text"] is not None

    def visualize(self):
        plt.imshow(self.image_data, interpolation='nearest')
        plt.show()

    def get_perm_onehot(self, perm_list):
        perm_onehot = np.zeros(len(perm_list), dtype=np.float32)
        for idx, perm in enumerate(perm_list):
            if perm in self.perm_set:
                perm_onehot[idx] = 1.0
        return perm_onehot

    def to_ui_perm_mapping(self, perm_list):
        """
        Return image-permission mapping
        :param sdk_map: sdk method-permission mapping from axplorer
        :param cp_map: content provider query-permission mapping from axplorer
        :return: (image,
                  ui_text_embedding, ui_resource_id_embedding,
                  elem_text_embedding, elem_resource_id_embedding,
                  perm_list_one_hot), i.e. ui-permission ready to be fed into NN

        image: dim 0 is ui element blocks,
               dim 1 is element interacted
        """
        return [self.image_data, \
                self.ui_text_embedding, self.ui_resource_id_embedding, \
                self.elem_text_embedding, self.elem_resource_id_embedding, \
                self.get_perm_onehot(perm_list)]

class DroidBotOutput(object):
    """
    This class is to parse DroidBot's output folder to UIEvent list
    Invalid files should be excluded at this stage
    """
    def __init__(self, config_json, input_dir):
        assert os.path.exists(input_dir), "DroidBot folder doesn't exist"

        # find package name
        dumpsys_candidates = [x for x in next(os.walk(input_dir))[2]
                              if "dumpsys" in x]
        assert len(dumpsys_candidates) == 1, "dumpsys file doesn't exist"
        dumpsys_filename = dumpsys_candidates[0]
        self.pkg_name = dumpsys_filename.split("_")[-1][:-len(".txt")]

        logcat_path = os.path.join(input_dir, "logcat.txt")
        assert os.path.exists(logcat_path), "logcat.txt doesn't exist"
        # load logcat
        logcat = LogCat(config_json, logcat_path, self.pkg_name).get_list()

        # load states
        states_folder_path = os.path.join(input_dir, "states")
        assert os.path.exists(states_folder_path), "states folder doesn't exist"
        state_hash_to_path = {} # {state_hash: state_path}
        state_paths = [os.path.join(states_folder_path, x)
                       for x in next(os.walk(states_folder_path))[2]
                       if ".json" in x]
        # load non-empty and in-app states only
        for state_path in state_paths:
            if os.stat(state_path).st_size != 0:
                with open(state_path, "r") as f:
                    state_json = json.load(f)
                    state_str = state_json["state_str"]
                    foreground_activity = state_json["foreground_activity"]
                    if self.pkg_name in foreground_activity:
                        state_hash_to_path[state_str] = state_path

        # load sdk_map and cp_map, and generate total perm list
        sdk_map = SDKMap(config_json).get_mapping()
        cp_map = CPMap(config_json).get_mapping()
        perm_set = set()
        for perm_list in sdk_map.values():
            perm_set.update(perm_list)
        for uri, method, perm_list in cp_map:
            perm_set.update(perm_list)
        perm_list = sorted(perm_set)

        # load text processors
        self.word_embedding = WordEmbedding(config_json).get_embedding()

        # load events
        events_folder_path = os.path.join(input_dir, "events")
        assert os.path.exists(events_folder_path), "events folder doesn't exist"
        event_ids = sorted([x[len("event_"):-len(".json")]
                            for x in next(os.walk(events_folder_path))[2]
                            if ".json" in x])
        # load non-empty events (including event json and trace)
        # the same event (by event_str) is united
        # load logcat entries as well
        event_hash_to_ui_perm_mapping = {} # {state_hash: state_path}
        logcat_idx = 0
        for event_idx, event_id in enumerate(event_ids):
            event_json_path = os.path.join(events_folder_path, "event_%s.json" % event_id)
            event_trace_path = os.path.join(events_folder_path, "event_trace_%s.trace" % event_id)
            if os.stat(event_json_path).st_size != 0 and \
               os.path.exists(event_trace_path) and \
               os.stat(event_trace_path).st_size != 0:

                with open(event_json_path, "r") as f1, open(event_trace_path) as f2:
                    event_json = json.load(f1)
                    event_hash = event_json["event_str"]
                    start_state_str = event_json["start_state"]
                    if start_state_str in state_hash_to_path:
                        state_path = state_hash_to_path[start_state_str]

                        # add logcat entries
                        curr_logcat_entries = []
                        while logcat_idx < len(logcat) and \
                              logcat[logcat_idx][0] < event_ids[event_idx]:
                            logcat_idx += 1
                        while logcat_idx < len(logcat) and \
                              (event_idx + 1 == len(event_ids) or \
                              logcat[logcat_idx][0] < event_ids[event_idx + 1]):
                            curr_logcat_entries.append(logcat[logcat_idx])
                            # print(logcat[logcat_idx])
                            logcat_idx += 1

                        ui_event = UIEvent(config_json,
                                           state_path,
                                           event_json_path,
                                           event_trace_path,
                                           curr_logcat_entries,
                                           sdk_map,
                                           cp_map,
                                           self.word_embedding)
                        # print(ui_event.perm_set)
                        # ui_event.visualize()
                        if event_hash not in event_hash_to_ui_perm_mapping:
                            event_hash_to_ui_perm_mapping[event_hash] = ui_event.to_ui_perm_mapping(perm_list)
                        else:
                            origin_perm_onehot = event_hash_to_ui_perm_mapping[event_hash][-1]
                            new_perm_onehot = ui_event.get_perm_onehot(perm_list)
                            event_hash_to_ui_perm_mapping[event_hash][-1] = np.maximum(origin_perm_onehot,
                                                                                       new_perm_onehot)
                        assert len(event_hash_to_ui_perm_mapping[event_hash]) == 6, "invalid ui_event"
        self.ui_perm_list = list(event_hash_to_ui_perm_mapping.values())

    def get_ui_perm_list(self):
        return self.ui_perm_list

    def get_pkg_name(self):
        return self.pkg_name

class TextCleaner(object):
    def __init__(self):
        from nltk.corpus import stopwords
        self.stop = stopwords.words("english")

        # used to convert isTestKey to is_test_key
        self.first_cap_re = re.compile("(.)([A-Z][a-z]+)")
        self.all_cap_re = re.compile("([a-z0-9])([A-Z])")

        # consider english only
        self.eng_re = re.compile("[a-z]+")

    def __id_convert(self, name):
        s1 = self.first_cap_re.sub(r"\1_\2", name)
        return self.all_cap_re.sub(r"\1_\2", s1).lower()

    def clean(self, text):
        alnum_str = re.sub(r"[^\w\s]", " ", text)
        raw_words = alnum_str.split()
        word_list = []
        for word in raw_words:
            if len(word) > 0:
                word_list += [x for x in self.__id_convert(word).split("_")
                              if x not in self.stop and self.eng_re.fullmatch(x) is not None]
        return word_list

class WordEmbedding(object):
    def __init__(self, config_json):
        word_embedding_path = config_json["word_embedding_path"]
        self.word_embedding = {}
        with open(word_embedding_path, "r") as f:
            entries = f.readlines()
            for entry in entries:
                fields = entry.strip().split()
                word = fields[0]
                embedding = np.array([float(x) for x in fields[1:]])
                self.word_embedding[word] = embedding

    def get_embedding(self):
        return self.word_embedding

def test_func_1():
    test_pkg_name = "com.accuweather.android"
    test_pkg_name_2 = "com.cam001.selfie"
    test_out_path = "/mnt/DATA_volume/lab_data/ui-code/%s/droidbot_out/" % test_pkg_name
    with open("config.json", "r") as f:
        config_json = json.load(f)
        logcat = LogCat(config_json, os.path.join(test_out_path, "logcat.txt.2"), test_pkg_name_2)
        sdk_map = SDKMap(config_json).get_mapping()
        cp_map = CPMap(config_json).get_mapping()
        ui_event = UIEvent(config_json,
            os.path.join(test_out_path, "states", "state_2019-01-14_140907.json"),
            os.path.join(test_out_path, "events", "event_2019-01-14_140930.json"),
            os.path.join(test_out_path, "events", "event_trace_2019-01-14_140930.trace"),
            logcat.get_list(),
            sdk_map,
            cp_map,
            WordEmbedding(config_json))
        # print(ui_event.perm_set)
        ui_event.visualize()

def test_func_2():
    test_text = "why_ads basBreaker HelloGuys! world talks"
    tc = TextCleaner()
    print(tc.clean(test_text))

if __name__ == "__main__":
    # test_func_1()
    test_func_2()
