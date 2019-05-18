import threading
import os
import subprocess

cluster_infos = [
    ["cluster1", 4],
    ["cluster2", 4],
    ["cluster3", 8],
    ["cluster4", 4],
    ["blacky", 8]
]
task_script_path = "/mnt/EXT_volume/projects_light/DroidGym/docker/droidgym/tasks/droidbot_trace_eval.sh"
run_script_path = "/mnt/EXT_volume/projects_light/DroidGym/docker/droidgym/run.sh"
qemu_path = "/home/yzy/qemu/droidbot-6.0-r3.qcow2"
output_dir = "/mnt/DATA_volume/lab_data/ui-code/trace_eval_out"
remote_dir = "/home/yzy/trace_eval/"

def scp_upload(remote_hostname, source_path, target_path):
    return subprocess.check_output(["scp", "-r", source_path, "%s:%s" % (remote_hostname, target_path)])

def scp_download(remote_hostname, source_path, target_path):
    return subprocess.check_output(["scp", "-r", "%s:%s" % (remote_hostname, source_path), target_path])

def ssh_command(remote_hostname, commands):
    return subprocess.check_output(["ssh", remote_hostname] + commands)

def run(remote_hostname, remote_idx, app_paths):
    for app_path in app_paths:
        pkg_name = app_path.split(os.path.sep)[-1][:-len(".apk")]

        result_dir = os.path.join(output_dir, pkg_name)
        if os.path.exists(result_dir):
            print("PASS %s" % pkg_name)
            continue
        else:
            print("RUNNING %s" % pkg_name)

        remote_idx_dir = os.path.join(remote_dir, str(remote_idx))
        remote_idx_result_dir = os.path.join(remote_idx_dir, "result")
        ssh_command(remote_hostname, ["mkdir", "-p", remote_idx_result_dir])

        # upload app, task.sh, run.sh
        remote_app_path = os.path.join(remote_idx_dir, "sample.apk")
        scp_upload(remote_hostname, app_path, remote_app_path)

        remote_task_script_path = os.path.join(remote_idx_dir, "task.sh")
        scp_upload(remote_hostname, task_script_path, remote_task_script_path)

        remote_run_script_path = os.path.join(remote_idx_dir, "run.sh")
        scp_upload(remote_hostname, run_script_path, remote_run_script_path)

        # run docker
        container_name = "%s-%s" % (remote_hostname, remote_idx)
        container_id = ssh_command(remote_hostname,
                                   ["docker", "ps", "-aqf", "name=%s" % container_name]).strip()
        if len(container_id) > 0:
            ssh_command(remote_hostname, ["docker", "rm", "-f", container_id])

        ssh_command(remote_hostname, ["bash",
                    remote_run_script_path,
                    remote_task_script_path,
                    remote_app_path,
                    remote_idx_result_dir,
                    qemu_path,
                    container_name])

        # download result
        scp_download(remote_hostname, remote_idx_result_dir, result_dir)

with open("app_list.txt", "r") as f:
    app_paths = [x.strip() for x in f.readlines()]
    cluster_assign = []
    for cluster_info in cluster_infos:
        for idx in range(cluster_info[1]):
            cluster_assign.append([cluster_info[0], idx, []])

    idx = 0
    for app_path in app_paths:
        cluster_assign[idx][2].append(app_path)
        idx = (idx + 1) % len(cluster_assign)

    os.makedirs(output_dir, exist_ok=True)

    thread_pool = [threading.Thread(target=run, args=(x)) for x in cluster_assign]
    for thread in thread_pool:
        thread.start()
    for thread in thread_pool:
        thread.join()

