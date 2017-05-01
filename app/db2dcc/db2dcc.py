#coding=utf-8

import argparse
import csv
import json
import os


def load_pscout(pscout_path):
    pscout_map = {}
    with open(pscout_path, "r") as pscout_file:
        next(pscout_file)
        reader = csv.reader(pscout_file)
        for row in reader:
            method_key = "%s %s" % (row[1], row[2])
            if method_key not in pscout_map:
                pscout_map[method_key] = set()
            if row[3] != "Parent":
                pscout_map[method_key].add(row[3])
    return pscout_map


def collector_func(apk_data_path_list, output_path, exclude_activities, pscout_map):
    """
    For each apk_data in apk_data_path_list,
    generate (viewContextStr, viewInfoStr, permission) tuples for each event.

    viewContextStr: activity, package, eventType
    viewInfoStr: screenX, screenY, thisWidth, thisHeight, rootWidth, rootHeight
    permission: use pscout
    """
    for apk_data_path in apk_data_path_list:
        # each trace tag corresponds to a start_state and end_state
        # need the start_state for to-access permission rules
        # discard the first trace here because it has no start_state

        # events      : [HOME_event, am start, back  , ...]
        # traces      :             [trace1  , trace2, ...]
        # start_state :                       [app   , ...]

        def load_jsons(json_path_list):
            json_list = []
            for json_path in json_path_list:
                with open(json_path, "r") as json_file:
                    json_list.append(json.load(json_file))
            return json_list

        def load_trace_perms(trace_path_list):
            with open("%s/dumpsys_package_%s.txt" %
                      (apk_data_path, apk_data_path.split("/")[-1])) as dumpsys_file:
                dumpsys_lines = dumpsys_file.readlines()

                granted_perms = set()
                line_idx = len(dumpsys_lines) - 1
                while dumpsys_lines[line_idx].strip() != "grantedPermissions:":
                    granted_perms.add(dumpsys_lines[line_idx].strip())
                    line_idx -= 1

                trace_perm_list = []
                for trace_path in trace_path_list:
                    curr_perm_set = set()
                    with open(trace_path, "r") as trace_file:
                        trace_lines = trace_file.readlines()
                    if len(trace_lines):
                        line_idx = 0
                        while trace_lines[line_idx].strip() != "*methods":
                            line_idx += 1
                        line_idx += 1
                        while trace_lines[line_idx].strip() != "*end":
                            fields = trace_lines[line_idx].split("\t")
                            method_key = "%s %s" % (fields[2], fields[3])
                            if method_key in pscout_map:
                                curr_perm_set |= pscout_map[method_key] & granted_perms
                            line_idx += 1
                    trace_perm_list.append(curr_perm_set)
                return trace_perm_list

        event_list = [os.path.join(dir_name, x)
                      for dir_name, _, files in os.walk("%s/events" % apk_data_path)
                      for x in files if x.endswith(".json")]
        event_list.sort()
        event_list = load_jsons(event_list)

        trace_list = [os.path.join(dir_name, x)
                      for dir_name, _, files in os.walk("%s/events" % apk_data_path)
                      for x in files if x.endswith(".trace")]
        trace_list.sort()
        trace_perm_list = load_trace_perms(trace_list)

        start_state_list = [os.path.join(dir_name, x)
                            for dir_name, _, files in os.walk("%s/states" % apk_data_path)
                            for x in files if x.endswith(".json")]
        start_state_list.sort()
        start_state_list = load_jsons(start_state_list)

        screenshot_list = [os.path.join(dir_name, x)
                           for dir_name, _, files in os.walk("%s/states" % apk_data_path)
                           for x in files if x.endswith(".png")]
        screenshot_list.sort()


def run(config_json_path):
    """
    parse config file and assign work to multiple processes
    """
    config_json = json.load(open(os.path.abspath(config_json_path), "r"))

    pscout_path = os.path.abspath(config_json["pscout_path"])
    pscout_map = load_pscout(pscout_path)

    droidbot_out_path = os.path.abspath(config_json["droidbot_out_dir"])
    output_path = os.path.abspath(config_json["output_dir"])
    exclude_activities = config_json["exclude_activities"]
    apk_data_path_list = ["%s/%s" % (droidbot_out_path, x)
                          for x in os.walk(droidbot_out_path).next()[1]]
    collector_func(apk_data_path_list, output_path, exclude_activities, pscout_map)


def parse_args():
    """
    parse command line input
    """
    parser = argparse.ArgumentParser(description="DroidBot out data to DroidCC rules")
    parser.add_argument("-c", action="store", dest="config_json_path",
                        required=True, help="path/to/db2dcc_config.json")
    options = parser.parse_args()
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.config_json_path)
    return


if __name__ == "__main__":
    main()
