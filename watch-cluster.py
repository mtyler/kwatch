#!/opt/homebrew/bin/python3
import argparse
import os
import time
import subprocess
import signal
import sys

interval = 5
do_ask = False

def get_namespaces():
    result = subprocess.run(['kubectl', 'get', 'ns', '-o', 'jsonpath={.items[*].metadata.name}'], capture_output=True, text=True)
    namespaces = result.stdout.split()
    return namespaces

def get_nodes():
    result = subprocess.run(['kubectl', 'get', 'no', '-o', 'jsonpath={.items[*].metadata.name}'], capture_output=True, text=True)
    nodes = result.stdout.split()
    return nodes

def view(title, show_me):
    #create an absraction layer that enables the user to refresh the current screen or continue
    os.system('clear')
    print(title)
    for each in show_me:
        print(f"\n{each[0]}")
        if isinstance(each[1], list):
            subprocess.run(each[1])
        else:
            subprocess.run(each[1], shell=True)
    
    cmd = rest()
    if cmd == 'r':
        view(title, show_me)
    elif cmd == 'x':
        watch_nodes()
    elif cmd == 'n':
        watch_ns()

def watch_ns():
    while True:
        show_me = []
        show_me.append(("Cluster Info:", ['kubectl', 'cluster-info']))
        show_me.append(("Nodes:", ['kubectl', 'get', 'no', '-o', 'wide']))
        show_me.append(("Conditions:", ['kubectl', 'get', 'no', '-o', 'jsonpath={range .items[*]}{.metadata.name}{": "}{range .status.conditions[*]}{.type}{"="}{.status}{" "}{end}{"\\n"}{end}']))
        show_me.append(("Storage Classes:", ['kubectl', 'get', 'sc', '-o', 'wide']))
        show_me.append(("Persistent Volumes:", ['kubectl', 'get', 'pv', '-o', 'wide']))
        ## Uncomment to display allocated resources as displayed in the node status object
        #show_me.append(("Allocated Resources:", ['kubectl', 'get', 'no', '-o', 'jsonpath={range .items[*]}{.metadata.name}{": cpu "}{.status.allocatable.cpu}{" mem "}{.status.allocatable.memory}{" eph-storage "}{.status.allocatable.ephemeral-storage}{"\\n"}{end}']))
        view('Cluster Overview', show_me)
        
        namespaces = get_namespaces()
        for ns in namespaces:
            show_me = []
            show_me.append(("Pods:", ['kubectl', 'get', 'po', '-n', ns, '-o', 'wide']))
            show_me.append(("Deployments:", ['kubectl', 'get', 'deploy', '-n', ns, '-o', 'wide']))
            show_me.append(("Services:", ['kubectl', 'get', 'svc', '-n', ns, '-o', 'wide']))
            view(f'Namespace: {ns}', show_me)
        
        # If auto scrolling is enabled, move to a watch nodes loop
        if interval > 0:
            watch_nodes()

def watch_nodes():
    while True:
        nodes = get_nodes()
        for node in nodes:
            show_me = []
            show_me.append((f"Pods:", ['kubectl', 'get', 'po', f'--field-selector=spec.nodeName={node}', '-A', '-o', 'wide']))
            show_me.append(("Allocated Memory:\tRequests\tLimits", f"kubectl describe node {node} | grep 'Allocated' -A 8 | grep 'memory'"))
            show_me.append(("Allocated CPU:\t\tRequests\tLimits", f"kubectl describe node {node} | grep 'Allocated' -A 8 | grep 'cpu'"))
            show_me.append(("Labels:", f"kubectl get node {node} -o jsonpath=\"{{.metadata.labels}}\""))
            show_me.append(("Taints:", f"kubectl get node {node} -o jsonpath=\"{{.spec.taints[*].key}}={{.spec.taints[*].effect}}\""))
            view(f'Node: {node}', show_me)

        # If auto scrolling is enabled, move to a watch namespaces loop
        if interval > 0:
            watch_ns()

##
# TODO
# Implement a method that shows deeper into cluster-wide resources
# aka cluster roles, cluster role bindings, secrets, config maps, etc. 
# def dig_deeper():
#
def rest():
    cmd = ''
    if do_ask:
        cmd = input("\nCtrl+c exit | r+Enter refresh | x+Enter nodes | n+Enter ns | Press Enter to continue:")
    else:
        time.sleep(interval)
    return cmd
    
def signal_handler(sig, frame): 
    sys.exit(0)

def print_to_log(message):
    log_file_path = os.path.join(os.path.dirname(__file__), f'{os.path.splitext(os.path.basename(__file__))[0]}.log')
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def parse_args():
    parser = argparse.ArgumentParser(description='Watch all pods in all namespaces.')
    parser.add_argument('--nodes', '-n', action='store_true', help='Watch all pods on all nodes')
    parser.add_argument('--interval', '-i', type=int, default=5, help='Interval between checks in seconds (default: 5)')
    parser.add_argument('--ask', action='store_true', help='Ask for confirmation before each iteration (default: False)')
    return parser.parse_args()

def main(args):
    args = parse_args()
    global interval
    global do_ask
    interval = args.interval
    do_ask = args.ask

    signal.signal(signal.SIGINT, signal_handler)

    # Begin watching namespaces
    watch_ns()

if __name__ == "__main__":
    main(sys.argv[1:])