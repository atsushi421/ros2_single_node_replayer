import argparse
import os
import time
from datetime import datetime

import rclpy
import yaml


def get_params_file_name(ns, node_name):
    ns_modified = ns
    if ns_modified[0] == '/':
        ns_modified = ns_modified[1:]
    params_file_name = ns_modified + "/" + node_name + ".yaml"
    return params_file_name.replace("/", "__")


def prepare_output_dir(params_file_name):
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    if not os.path.isdir("output"):
        os.mkdir("output")
    os.chdir("output")

    logdir = datetime.now().strftime("%Y-%m-%d-%H-%M-%S_") + params_file_name[:-len(".yaml")]
    os.mkdir(logdir)
    os.chdir(logdir)


def main(node_name, ns, package_name, executable_name, remappings):
    rclpy.init()
    node = rclpy.create_node("node_input_topic_recorder")

    # Need to wait for slow discovery protocol
    time.sleep(5)

    # names = node.get_node_names()
    info = node.get_subscriber_names_and_types_by_node(node_name, ns)

    params_file_name = get_params_file_name(ns, node_name)
    prepare_output_dir(params_file_name)

    os.system(f"ros2 param dump {ns}/{node_name} > {params_file_name}")

    record_command = "ros2 bag record /tf /tf_static"
    for topic_and_types in info:
        topic, types = topic_and_types
        record_command = record_command + " " + topic
    os.system(record_command)

    with open("ros2_run_" + package_name + "_" + executable_name, "w") as f:
        exec_command = "ros2 run " + package_name + " " + executable_name + \
                       " --ros-args --params-file " + params_file_name + \
                       " -r __ns:=" + ns + " -r __node:=" + node_name

        for k, v in remappings.items():
            exec_command = exec_command + " -r " + k + ":=" + v

        f.write(exec_command)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record input topic data for the target node")
    parser.add_argument("complete_node_info", type=str, help="target complete node info")
    args = parser.parse_args()

    with open(args.complete_node_info, 'r') as f:
        node_info = yaml.safe_load(f)

    main(
        node_info['node_name'],
        node_info['namespace'],
        node_info['package_name'],
        node_info['executable'],
        node_info['remappings']
    )
