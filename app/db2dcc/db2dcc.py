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


def assemble_perm_rules(apk_data_path_list, output_path, exclude_activities, pscout_map):
    """
    For each apk_data in apk_data_path_list,
    generate (viewContextStr, viewInfoStr, permission) tuples for each event.

    params:

    viewContextStr: activity, package, eventType
    viewInfoStr: screenX, screenY, thisWidth, thisHeight, rootWidth, rootHeight
    permission: use pscout

    return:

    """
    start_perm_rules = {}
    ui_perm_rules = {}

    for apk_data_path in apk_data_path_list:
        # each trace tag corresponds to a start_state and end_state
        # need the start_state for to-access permission rules
        # discard the first trace here because it has no start_state

        # events      : [HOME_event, am start, back  , ...]
        # traces      :             [trace1  , trace2, ...]
        # start_state :                       [app   , ...]

        package_name = apk_data_path.split("/")[-1]

        def load_jsons(json_path_list):
            json_list = []
            for json_path in json_path_list:
                with open(json_path, "r") as json_file:
                    json_list.append(json.load(json_file))
            return json_list

        def load_trace_perms(trace_path_list):
            with open("%s/dumpsys_package_%s.txt" %
                      (apk_data_path, package_name)) as dumpsys_file:
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
                    trace_perm_list.append(list(curr_perm_set))
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

        # start_perm_rule:
        # {"packageName": ..., "permission": []}
        start_perm_rules[package_name] = list(trace_perm_list[0])

        # UI_perm_rules:
        # {<viewContextStr>: {"viewInfoStr": ..., "permission": [], "screenshotPath": ...}}
        event_list = event_list[2:]
        trace_perm_list = trace_perm_list[1:]

        for rule_tuple in zip(event_list, trace_perm_list, start_state_list, screenshot_list):
            event = rule_tuple[0]
            trace_perm = rule_tuple[1]
            state = rule_tuple[2]
            screenshot = rule_tuple[3]

            activity = state["foreground_activity"]
            if activity in exclude_activities:
                continue
            if not len(trace_perm):
                continue

            if event["event"]["event_type"] == "touch":
                view_ctx_str = "activity=%s;package=%s;view_action_id=0" % (activity, package_name)
                x = event["event"]["x"]
                y = event["event"]["y"]
                this_view = None
                for view in state["views"]:
                    if view["bounds"][0][0] <= x <= view["bounds"][1][0] and \
                       view["bounds"][0][1] <= y <= view["bounds"][1][1]:
                       # pre-order walking
                        this_view = view
                if this_view is None:
                    continue
            elif event["event"]["event_type"] == "key" and \
                 event["event"]["name"] == "BACK":
                view_ctx_str = "activity=%s;package=%s;view_action_id=1" % (activity, package_name)
                this_view = state["views"][0]
                for view in state["views"]:
                    if view["focused"]:
                        this_view = view
                        break
            else:
                continue

            this_rect = "%d %d %d %d" % (this_view["bounds"][0][0],
                                         this_view["bounds"][0][1],
                                         this_view["bounds"][1][0],
                                         this_view["bounds"][1][1])
            root_rect = "%d %d %d %d" % (state["views"][0]["bounds"][0][0],
                                         state["views"][0]["bounds"][0][1],
                                         state["views"][0]["bounds"][1][0],
                                         state["views"][0]["bounds"][1][1])
            view_info_str = "thisRect=%s;rootRect=%s;thisResId=%s;rootResId=%s" % \
                            (this_rect, root_rect, this_view["resource_id"], state["views"][0]["resource_id"])

            if package_name not in ui_perm_rules:
                ui_perm_rules[package_name] = {}
            if activity not in ui_perm_rules[package_name]:
                ui_perm_rules[package_name][activity] = {}
            if view_ctx_str not in ui_perm_rules[package_name][activity]:
                ui_perm_rules[package_name][activity][view_ctx_str] = []
            ui_perm_rules[package_name][activity][view_ctx_str].append({
                "viewInfoStr": view_info_str,
                "permission": trace_perm,
                "screenshotPath": screenshot,
                "event": event["tag"],
            })

    return start_perm_rules, ui_perm_rules


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
    start_perm_rules, ui_perm_rules = assemble_perm_rules(apk_data_path_list,
                                                          output_path,
                                                          exclude_activities,
                                                          pscout_map)

    print json.dumps(ui_perm_rules, indent=2)


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
