#!/opt/homebrew/bin/python3
import argparse
import signal
import subprocess
import sys
import os
import json
import time



def tail_logs(ns, labels):

# This yaml defines Namespaces and Labels within that namespace to gather logs
#k logs -n gateway --all-containers=true -l app=openelb
#k logs -n gateway --all-containers=true -l job-name=openelb-admission-patch
#k logs -n gateway --all-containers=true -l app.kubernetes.io/instance=ngf
    # build kubectl command
    cmd = ['kubectl', 'logs', '-n', ns, '--all-containers=true', '-f']
    for label in labels:
        cmd.append(f'-l {label}')

    for i in cmd:
        mystring = ' '.join(cmd)

    print(f"Running command: {mystring}")
    while True:
        try:
            subprocess.run( cmd, check=True )
        except subprocess.CalledProcessError as e:
            print(f"kubectl logs command failed with error: {e}...")
            time.sleep(5)


def validate_namespace(ns):
    result = subprocess.run(['kubectl', 'get', 'ns', ns, '-o', 'jsonpath={.metadata.name}', '--no-headers'], capture_output=True, text=True)
    #result = subprocess.run(['kubectl', 'get', 'namespace', ns, '--no-headers', '-o', "jsonpath={.metadata.name}"], capture_output=True, check=True, text=True)
    if ns == result.stdout:
        return True
    else:
        return False

def read_config():
    # Determine the path to the config file
    script_path = os.path.abspath(__file__)
    config_file_path = os.path.splitext(script_path)[0] + '.json'
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)
    return config

def get_namespace(config):
    warn = []
    spaces = []
    for namespace in config.keys():
        if validate_namespace(namespace):
            spaces.append(namespace)
        else:
            warn.append(namespace)

    if warn:
        print("Invalid Namespaces:")
        for w in warn:
            print(f"    {w}")
    if spaces:
        print("Choose a Namespace to watch:")
        for s in spaces:
            print(f"    {s}")
    while True:
        cmd_in = input("* = all: ")
        # validate entry
        if cmd_in == "*" or cmd_in in spaces:
            return cmd_in
        else:
            print("Invalid request: " + cmd_in)

def get_pod_status(ns, labels):
    cmd = ['kubectl', 'get', 'pods', '-n', ns, '-o', 'jsonpath=\'{range .items[*]}{.metadata.name}{"="}{.status.phase}{" "}{end}\'']
    for l in labels:
        this_cmd = cmd.copy()
        this_cmd.append(f'-l {l}')
        result = subprocess.run(this_cmd, capture_output=True, text=True)
        for pod in result.stdout.strip("'").split():
            pod_info = pod.split('=')
            print(f"Pod: {pod_info[0]}\t\t\t\t{pod_info[1]}")
    return

def get_containers(labels, ns):
    containers = []
    for label in labels:
        cmd = ['kubectl', 'get', 'pods', '-n', ns, '-l', label, '-o', 'jsonpath={.items[*].spec.containers[*].name}']
#        for i in cmd:
#            mystring = ' '.join(cmd)
#        print(f"Running command: {mystring}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        for i in result.stdout.split():
            containers.append(i)
    return containers

def get_labels(config, ns):
    labels = []
    for label in config[ns]:
        labels.append(label)
    return labels

def signal_handler(sig, frame): 
    sys.exit(0)

def parse_args():
    parser = argparse.ArgumentParser(description='Watch all pods in all namespaces.')
    return parser.parse_args()

def main(args):
    args = parse_args()
    signal.signal(signal.SIGINT, signal_handler)

    config = read_config()
    # Get user input
    ns = get_namespace(config)

    labels = get_labels(config, ns)
    #print(labels)
    
    get_pod_status(ns, labels)
    
#    containers = get_containers(labels, ns)
#    for c in containers:
#        print(c)
#
    #tail_logs(ns, labels)

if __name__ == "__main__":
    main(sys.argv)