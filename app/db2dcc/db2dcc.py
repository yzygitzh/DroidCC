#coding=utf-8

import argparse
import json
import os
import re
import subprocess

from PIL import Image, ImageDraw


TRACE_VERSION_RE = re.compile(r"VERSION: ([0-9]+)")
TRACE_NUM_RE = re.compile(r"Threads \(([0-9]+)\):")
TRACE_ITEM_RE = re.compile(r"([0-9]+)[ \t]+(ent|xit|unr)(!*)[ \t]+([0-9]+)[ \-\+][\.]*([^ \t]+)[ \t]+([^ \t]+)[ \t]+([^ \t]+)")


def java_shorty2full(short_sig):
    basic_type_mapping = {
        "Z": "boolean",
        "B": "byte",
        "C": "char",
        "S": "short",
        "I": "int",
        "J": "long",
        "F": "float",
        "D": "double",
        "V": "void"
    }
    fields = short_sig.split()
    idx = 1
    array_depth = 0
    parsed_paras = []
    # while fields[1][idx] != ")":
    while idx < len(fields[1]):
        if fields[1][idx] == "L":
            class_end_idx = idx
            while fields[1][class_end_idx] != ";":
                class_end_idx += 1
            parsed_paras.append(fields[1][idx + 1:class_end_idx].replace("/", ".") + array_depth * "[]")
            idx = class_end_idx
            array_depth = 0
        elif fields[1][idx] == "[":
            array_depth += 1
        elif fields[1][idx] != ")":
            parsed_paras.append(basic_type_mapping[fields[1][idx]] + array_depth * "[]")
            array_depth = 0
        idx += 1
    return fields[0] + "(%s)%s" % (",".join(parsed_paras[:-1]), parsed_paras[-1])


def load_axplorer(axplorer_paths):
    axplorer_map = {}
    sdk_mapping_path = axplorer_paths["sdk"]
    cp_mapping_path = axplorer_paths["cp"]

    with open(sdk_mapping_path, "r") as sdk_mapping_file:
        lines = sdk_mapping_file.read().splitlines()
        for line in lines:
            method_sig, perms = line.split("  ::  ")
            perm_set = set(perms.split(", "))
            if method_sig not in axplorer_map:
                axplorer_map[method_sig] = set()
            axplorer_map[method_sig] |= perm_set

    with open(cp_mapping_path, "r") as cp_mapping_file:
        lines = cp_mapping_file.read().splitlines()
        for line in lines:
            fields = line.split("  ")
            perm = fields[-1]
            if perm.startswith("["):
                continue
            method_sig = fields[0]
            if method_sig not in axplorer_map:
                axplorer_map[method_sig] = set()
            axplorer_map[method_sig].add(perm)

    return axplorer_map


def match_axplorer_map(target_str, axplorer_map):
    if target_str in axplorer_map:
        return target_str
    fields = target_str.split("(")
    content_case_str = "%s(%s" % (".".join(fields[0].split(".")[:-1]),
                                  fields[1])
    if content_case_str in axplorer_map:
        return content_case_str
    return None


def assemble_perm_rules(apk_data_path_list, output_path, exclude_activities, axplorer_map):
    """
    For each apk_data in apk_data_path_list,
    generate (viewContextStr, viewInfoStr, permission) tuples for each event.

    params:

    viewContextStr: activity, package, eventType
    viewInfoStr: screenX, screenY, thisWidth, thisHeight, rootWidth, rootHeight
    permission: use pscout

    return:

    """
    os.system("mkdir -p %s/perm_rules" % output_path)
    os.system("mkdir -p %s/screenshots" % output_path)

    for apk_data_path in apk_data_path_list:
        # each trace tag corresponds to a start_state and end_state
        # need the start_state for to-access permission rules
        # discard the first trace here because it has no start_state

        # events      : [HOME_event, am start, back  , ...]
        # traces      :             [trace1  , trace2, ...]
        # start_state :                       [app   , ...]
        start_perm_rules = {}
        ui_perm_rules = {}

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
                # each element in the list is a dict -> {(tid, tname): {"method", perm_set}}
                trace_perm_list = []
                for trace_path in trace_path_list:
                    p = subprocess.Popen(["dmtracedump", "-o", trace_path], stdout=subprocess.PIPE)
                    trace_str = p.communicate()[0].decode()

                    trace_lines = trace_str.split(os.linesep)
                    if len(trace_lines) <= 1:
                        continue

                    idx = 1
                    thread_num = int(TRACE_NUM_RE.match(trace_lines[idx]).groups()[0])
                    idx += 1

                    tid2tname = {}
                    for i in range(thread_num):
                        thread_name_start_idx = trace_lines[i + idx].find(" ") + 1
                        tname = trace_lines[i + idx][thread_name_start_idx:]
                        tid = int(trace_lines[i + idx][:thread_name_start_idx])
                        tid2tname[tid] = tname
                    idx += thread_num + 1

                    trace_obj = {}
                    while len(trace_lines[idx]):
                        line_info = TRACE_ITEM_RE.match(trace_lines[idx]).groups()
                        tid = int(line_info[0])

                        method_record = "%s %s" % (line_info[4], line_info[5])
                        if method_record[0].isalpha():
                            method_key = java_shorty2full(method_record)
                            perm_map_key = match_axplorer_map(method_key, axplorer_map)
                            if perm_map_key is not None:
                                perm_set = axplorer_map[perm_map_key] & granted_perms
                                if len(perm_set):
                                    if tid not in trace_obj:
                                        trace_obj[tid] = {"name": tid2tname[tid], "perm": {}}
                                    trace_obj[tid]["perm"][method_key] = list(perm_set)
                        idx += 1

                    trace_perm_list.append(trace_obj)
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

        event_common_tags = sorted(set(event_tag_list) & set(trace_tag_list))[:10]
        event_common_tags.sort()
        state_common_tags = sorted(set(state_tag_list) & set(screenshot_tag_list))
        state_common_tags.sort()

        event_list = load_jsons(["%s%s%s" % (event_path_pair[0], x, event_path_pair[1])
                                 for x in event_common_tags])
        trace_perm_list = load_trace_perms(["%s%s%s" % (trace_path_pair[0], x, trace_path_pair[1])
                                            for x in event_common_tags])

        state_list = load_jsons(["%s%s%s" % (state_path_pair[0], x, state_path_pair[1])
                                 for x in state_common_tags])
        state_dict = {x["state_str"]: x for x in state_list}
        screenshot_list = ["%s%s%s" % (screenshot_path_pair[0], x, screenshot_path_pair[1])
                           for x in state_common_tags]
        screenshot_dict = {state_list[x]["state_str"]: screenshot_list[x]
                           for x in range(len(state_list))}

        # start_perm_rule:
        # {"packageName": ..., "permission": []}
        start_perm_rules[package_name] = load_trace_perms([
            "%s%s%s" % (trace_path_pair[0], trace_tag_list[0], trace_path_pair[1])
        ])[0]

        # UI_perm_rules:
        # {<viewContextStr>: {"viewInfoStr": ..., "permission": [], "screenshotPath": ...}}

        for rule_tuple in zip(event_list, trace_perm_list):
            event = rule_tuple[0]
            trace_perm = rule_tuple[1]
            state_str = event["start_state"]
            if state_str not in state_dict:
                print(state_str)
                continue
            state = state_dict[state_str]
            screenshot = screenshot_dict[state_str]

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
        # no rules
        if package_name not in ui_perm_rules:
            ui_perm_rules[package_name] = {}
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
            print(start_perm_rules)
            print(ui_perm_rules)
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
    config_json = json.load(open(config_json_path, "r"))

    axplorer_paths = config_json["axplorer_paths"]
    axplorer_map = load_axplorer(axplorer_paths)

    droidbot_out_path = os.path.abspath(config_json["droidbot_out_dir"])
    output_path = os.path.abspath(config_json["output_dir"])
    exclude_activities = config_json["exclude_activities"]
    apk_data_path_list = ["%s/%s" % (droidbot_out_path, x)
                          for x in next(os.walk(droidbot_out_path))[1]]

    assemble_perm_rules(apk_data_path_list, output_path, exclude_activities, axplorer_map)


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
