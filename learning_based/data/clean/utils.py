#coding=utf-8

import json
import numpy as np
import os
import re
import traceback

import datetime
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
                        ts += datetime.timedelta(self.timezone_diff)
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
                 sdk_map, cp_map):
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

        self.state_path = state_path
        self.event_path = event_path
        self.trace_path = trace_path

        self.logcat = logcat

        self.sdk_map = sdk_map
        self.cp_map = cp_map

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
        for view in self.state["views"]:
            if len(view["children"]) == 0:
                draw_dim = self.text_dim if self.__is_text_view(view) else self.image_dim
                self.__color_view(view, draw_dim)

        # color the interacted element
        if "view" in self.event["event"]:
            self.__color_view(self.event["event"]["view"], self.interact_dim)

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

    def __color_view(self, view, draw_dim):
        """
        Color the view in self.image_data given the dimension to color.
        """
        # draw view
        bounds = view["bounds"]
        x_min = max(0, int(bounds[0][0] * self.down_ratio))
        y_min = max(0, int(bounds[0][1] * self.down_ratio))
        x_max = min(self.down_dim[0] - 1, int((bounds[1][0] - 1) * self.down_ratio))
        y_max = min(self.down_dim[1] - 1, int((bounds[1][1] - 1) * self.down_ratio))
        if x_min >= x_max or y_min >= y_max:
            return
        self.image_data[x_min:x_max, y_min:y_max, draw_dim] = 1.0
        # draw view's four boundaries
        self.image_data[x_min - 1:x_min, y_min - 1:y_max + 1, draw_dim] = 0.0
        self.image_data[x_max:x_max + 1, y_min - 1:y_max + 1, draw_dim] = 0.0
        self.image_data[x_min - 1:x_max + 1, y_min - 1:y_min, draw_dim] = 0.0
        self.image_data[x_min - 1:x_max + 1, y_max:y_max + 1, draw_dim] = 0.0

    def __is_text_view(self, view):
        if "text" not in view:
            return False
        return "edittext" in view["class"].lower()

    def visualize(self):
        plt.imshow(self.image_data, interpolation='nearest')
        plt.show()

    def to_ui_perm_mapping(self, perm_list):
        """
        Return image-permission mapping
        :param sdk_map: sdk method-permission mapping from axplorer
        :param cp_map: content provider query-permission mapping from axplorer
        :return: (image, perm_list_one_hot) ui-permission ready to be fed into NN

        image: dim 0 is ui element blocks,
               dim 1 is element interacted
        """
        perm_onehot = np.zeros(len(perm_list), dtype=np.float32)
        for idx, perm in enumerate(perm_list):
            if perm in self.perm_set:
                perm_onehot[idx] = 1.0
        return self.image_data, perm_onehot

if __name__ == "__main__":
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
            cp_map)
        print(ui_event.perm_set)
        ui_event.visualize()
