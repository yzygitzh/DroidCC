#coding=utf-8

import argparse
import csv
import json
import os

from PIL import Image, ImageDraw


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

    os.system("mkdir -p %s/perm_rules" % output_path)
    os.system("mkdir -p %s/screenshots" % output_path)

    for apk_data_path in apk_data_path_list:
        # each trace tag corresponds to a start_state and end_state
        # need the start_state for to-access permission rules
        # discard the first trace here because it has no start_state

        # events      : [HOME_event, am start, back  , ...]
        # traces      :             [trace1  , trace2, ...]
        # start_state :                       [app   , ...]

        package_name = apk_data_path.split("/")[-1]
        print(package_name)

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
                line_idx = 0
                while dumpsys_lines[line_idx].strip() != "requested permissions:":
                    line_idx += 1
                line_idx += 1
                while dumpsys_lines[line_idx].strip() != "install permissions:":
                    granted_perms.add(dumpsys_lines[line_idx].strip())
                    line_idx += 1

                # TODO: filter background services
                trace_perm_list = []
                for trace_path in trace_path_list:
                    curr_perm_set = set()
                    with open(trace_path, "rb") as trace_file:
                        trace_lines = trace_file.readlines()
                    if len(trace_lines):
                        line_idx = 0
                        while trace_lines[line_idx].strip() != b"*methods":
                            line_idx += 1
                        line_idx += 1
                        while trace_lines[line_idx].strip() != b"*end":
                            fields = trace_lines[line_idx].decode().split("\t")
                            method_key = "%s %s" % (fields[2], fields[3])
                            if method_key in pscout_map:
                                curr_perm_set |= pscout_map[method_key] & granted_perms
                            line_idx += 1
                    trace_perm_list.append(list(curr_perm_set))
                return trace_perm_list

        event_path_pair = ("%s/events/event_" % apk_data_path, ".json")
        trace_path_pair = ("%s/events/event_trace_" % apk_data_path, ".trace")
        state_path_pair = ("%s/states/state_" % apk_data_path, ".json")
        screenshot_path_pair = ("%s/states/screen_" % apk_data_path, ".jpg")

        event_tag_list = [x[len("event_"):-len(".json")]
                          for x in next(os.walk("%s/events" % apk_data_path))[2]
                          if x.endswith(".json")]
        trace_tag_list = [x[len("event_trace_"):-len(".trace")]
                          for x in next(os.walk("%s/events" % apk_data_path))[2]
                          if x.endswith(".trace")]
        state_tag_list = [x[len("state_"):-len(".json")]
                          for x in next(os.walk("%s/states" % apk_data_path))[2]
                          if x.endswith(".json")]
        screenshot_tag_list = [x[len("screen_"):-len(".jpg")]
                               for x in next(os.walk("%s/states" % apk_data_path))[2]
                               if x.endswith(".jpg")]

        common_tags = list(set(event_tag_list) & set(trace_tag_list) &
                           set(state_tag_list) & set(screenshot_tag_list))
        common_tags.sort()

        event_list = load_jsons(["%s%s%s" % (event_path_pair[0], x, event_path_pair[1])
                                 for x in common_tags])
        trace_perm_list = load_trace_perms(["%s%s%s" % (trace_path_pair[0], x, trace_path_pair[1])
                                            for x in common_tags])
        state_list = load_jsons(["%s%s%s" % (state_path_pair[0], x, state_path_pair[1])
                                 for x in common_tags])
        screenshot_list = ["%s%s%s" % (screenshot_path_pair[0], x, screenshot_path_pair[1])
                           for x in common_tags]

        # start_perm_rule:
        # {"packageName": ..., "permission": []}
        start_perm_rules[package_name] = load_trace_perms([
            "%s%s%s" % (trace_path_pair[0], trace_tag_list[0], trace_path_pair[1])
        ])[0]

        # UI_perm_rules:
        # {<viewContextStr>: {"viewInfoStr": ..., "permission": [], "screenshotPath": ...}}

        for rule_tuple in zip(event_list, trace_perm_list, state_list, screenshot_list):
            event = rule_tuple[0]
            trace_perm = rule_tuple[1]
            state = rule_tuple[2]
            screenshot = rule_tuple[3]

            activity = state["foreground_activity"]
            if activity in exclude_activities:
                continue
            elif "/." in activity:
                activity = activity.replace("/", "")
            else:
                activity = activity.split("/")[1]

            if not len(trace_perm):
                continue

            if event["event"]["event_type"] == "touch":
                view_ctx_str = "activity=%s;package=%s;view_action_id=0" % (activity, package_name)
                this_view = None
                for view in state["views"]:
                    if match_touched_view(event, view):
                       # pre-order walking
                        this_view = view
                if this_view is None:
                    continue
            elif event["event"]["event_type"] == "key" and \
                 event["event"]["name"] == "BACK":
                if not len(state["views"]):
                    continue
                view_ctx_str = "activity=%s;package=%s;view_action_id=1" % (activity, package_name)
                this_view = state["views"][0]
                for view in state["views"]:
                    if view["focused"]:
                        this_view = view
                        break
            else:
                continue

            # a little smaller to get rid of 0.5 in Rect Java class...
            this_rect = "%d %d %d %d" % (this_view["bounds"][0][0] + 2,
                                         this_view["bounds"][0][1] + 2,
                                         this_view["bounds"][1][0] - 2,
                                         this_view["bounds"][1][1] - 2)
            root_rect = "%d %d %d %d" % (state["views"][0]["bounds"][0][0],
                                         state["views"][0]["bounds"][0][1],
                                         state["views"][0]["bounds"][1][0],
                                         state["views"][0]["bounds"][1][1])
            view_info_str = "thisRect=%s;rootRect=%s;thisResId=%s;rootResId=%s" % \
                            (this_rect, root_rect,
                             this_view["resource_id"], state["views"][0]["resource_id"])

            if package_name not in ui_perm_rules:
                ui_perm_rules[package_name] = {}
            if activity not in ui_perm_rules[package_name]:
                ui_perm_rules[package_name][activity] = []
            ui_perm_rules[package_name][activity].append({
                "viewCtxStr": view_ctx_str,
                "viewInfoStr": view_info_str,
                "permission": trace_perm,
                "screenshotPath": screenshot,
                "eventTag": event["tag"],
                "eventType": "BACK" if "name" in event["event"] else "TOUCH",
                "bounds": this_view["bounds"]
            })
        # output screenshots
        for activity in ui_perm_rules[package_name]:
            for view_info in ui_perm_rules[package_name][activity]:
                jpg_path = view_info.pop("screenshotPath")
                jpg_tag = view_info["eventTag"]
                bounds = view_info["bounds"]
                im = Image.open(jpg_path)
                draw = ImageDraw.Draw(im)
                for i in range(-5, 5):
                    draw.rectangle([
                        bounds[0][0] - i, bounds[0][1] - i,
                        bounds[1][0] + i, bounds[1][1] + i
                    ], outline=(153, 204, 51, 255 + 10 * (i - 5)))
                del draw
                with open("%s/screenshots/%s.jpg" % (output_path, jpg_tag), "wb") as out_jpg_file:
                    im.save(out_jpg_file)

        # output perm rules
        with open("%s/perm_rules/%s.json" % (output_path, package_name), "w") as output_file:
            json.dump({
                "start_perm_rules": start_perm_rules[package_name],
                "ui_perm_rules": ui_perm_rules[package_name]
            }, output_file, indent=2)


def match_touched_view(touch_event, view):
    x = touch_event["event"]["x"]
    y = touch_event["event"]["y"]
    bounds = touch_event["event"]["view"]["bounds"]
    if bounds is not None and \
       bounds == view["bounds"]:
        return True
    if x is not None and y is not None and \
       view["bounds"][0][0] <= x <= view["bounds"][1][0] and \
       view["bounds"][0][1] <= y <= view["bounds"][1][1]:
        return True
    return False


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
                          for x in next(os.walk(droidbot_out_path))[1]]

    assemble_perm_rules(apk_data_path_list, output_path, exclude_activities, pscout_map)


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
