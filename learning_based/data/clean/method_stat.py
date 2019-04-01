#coding=utf-8

import argparse
import json
import os
import traceback

def run(input_dir, output_path):
    apkpure_dir = os.path.join(input_dir, "apkpure")
    app_categories = next(os.walk(apkpure_dir))[1]
    method_count = {}
    for category in app_categories:
        print(category)
        category_dir = os.path.join(apkpure_dir, category)
        apps = next(os.walk(category_dir))[1]
        app_count = 0
        for app in apps:
            app_count += 1
            print(app)
            print(app_count, "/", len(apps))
            event_dir = os.path.join(category_dir, app, "droidbot_out", "events")
            if os.path.exists(event_dir):
                traces = [x for x in next(os.walk(event_dir))[2]
                          if x.endswith(".trace")]
                for trace in traces:
                    trace_path = os.path.join(event_dir, trace)
                    if os.stat(trace_path).st_size > 0:
                        try:
                            with open(trace_path, "r") as f:
                                trace_lines = f.readlines()
                                idx = 0
                                while idx < len(trace_lines) and \
                                    not trace_lines[idx].startswith("*methods"):
                                    idx += 1
                                idx += 1
                                while idx < len(trace_lines) and \
                                    not trace_lines[idx].startswith("*end"):
                                    fields = trace_lines[idx].split()
                                    method = ".".join([fields[1], fields[2]])
                                    if method not in method_count:
                                        method_count[method] = 0
                                    method_count[method] += 1
                                    idx += 1
                        except:
                            traceback.print_exc()

    with open(output_path, "w") as f:
        json.dump(sorted(method_count.items(), key=lambda x : x[1], reverse=True), f, indent=2)

def parse_args():
    parser = argparse.ArgumentParser(description="DroidCC method statistic script")
    parser.add_argument("-i", action="store", dest="input_dir",
                        required=True, help="path/to/out_humanoid")
    parser.add_argument("-o", action="store", dest="output_path",
                        required=True, help="path/to/output_file.json")
    options = parser.parse_args()
    return options

def main():
    opts = parse_args()
    run(opts.input_dir, opts.output_path)
    return

if __name__ == "__main__":
    main()
