#!/opt/homebrew/bin/python3
import argparse
import os
import time
import subprocess
import signal
import sys

interval = 5
do_ask = False
debug = False

class Page:
    debug = True
    def __init__(self, title, commands):
        self.title = title
        self.commands = commands

    def display(self):
        os.system('clear')
        print(self.title)
        for each in self.commands:
            print(f"\n{each[0]}")
            if isinstance(each[1], list):
                if debug: print(f'debug: {each[1]}')
                subprocess.run(each[1])
            else:
                if debug: print(f'debug: {each[1]}')
                subprocess.run(each[1], shell=True)

    def refresh(self):
        self.display()
        cmd = rest()
        if cmd == 'r':
            self.refresh()
        elif cmd == 'x':
            watch_nodes()
        elif cmd == 'n':
            watch_ns()

def get_namespaces():
    result = subprocess.run(['kubectl', 'get', 'ns', '-o', 'jsonpath={.items[*].metadata.name}'], capture_output=True, text=True)
    namespaces = result.stdout.split()
    return namespaces

def get_nodes():
    result = subprocess.run(['kubectl', 'get', 'no', '-o', 'jsonpath={.items[*].metadata.name}'], capture_output=True, text=True)
    nodes = result.stdout.split()
    return nodes

def get_pod_by_label(ns, label):
    result = subprocess.run(['kubectl', 'get', 'po', '-n', ns, '-l', label, '-o', 'jsonpath={.items[*].metadata.name}'], capture_output=True, text=True)
    pods = result.stdout.split()
    return pods

def view_page(title, commands):
    page = Page(title, commands)
    page.refresh()

def watch(nodes):
    if nodes:
        watch_nodes()
    else:
        watch_ns()

def watch_ns():
    while True:
        page = []
        page.append(("Cluster Info:", ['kubectl', 'cluster-info']))
        page.append(("Nodes:", ['kubectl', 'get', 'no', '-o', 'wide']))
        page.append(("Conditions:", ['kubectl', 'get', 'no', '-o', 'jsonpath={range .items[*]}{.metadata.name}{": "}{range .status.conditions[*]}{.type}{"="}{.status}{" "}{end}{"\\n"}{end}']))
        page.append(("Storage Classes:", ['kubectl', 'get', 'sc', '-o', 'wide']))
        page.append(("Persistent Volumes:", ['kubectl', 'get', 'pv', '-o', 'wide']))
        ## Uncomment to display allocated resources as displayed in the node status object
        #page.append(("Allocated Resources:", ['kubectl', 'get', 'no', '-o', 'jsonpath={range .items[*]}{.metadata.name}{": cpu "}{.status.allocatable.cpu}{" mem "}{.status.allocatable.memory}{" eph-storage "}{.status.allocatable.ephemeral-storage}{"\\n"}{end}']))
        view_page('Cluster Overview', page)
        
#        page = []
#        page.append(("Rook Ceph Toolbox:", ['kubectl', 'logs', '-n', 'rook-ceph', 'jobs/rook-ceph-toolbox-job', 'script']))
#        view_page('Storage Overview', page)
        
        namespaces = get_namespaces()
        for ns in namespaces:
            page = []
            page.append(("Pods:", ['kubectl', 'get', 'po', '-n', ns, '-o', 'wide']))
            page.append(("Deployments:", ['kubectl', 'get', 'deploy', '-n', ns, '-o', 'wide']))
            page.append(("Services:", ['kubectl', 'get', 'svc', '-n', ns, '-o', 'wide']))
            if ns == 'cert-manager':
                page.append(("Logs:", ['kubectl', 'logs', '-n', ns, '-l', "app.kubernetes.io/instance=cert-manager", '--tail=5']))
            #if ns == 'rook-ceph':    

            view_page(f'Namespace: {ns}', page)
        
            if ns == 'rook-ceph':
                page = []
                pod_names = get_pod_by_label(ns,' app=rook-ceph-tools')
                page.append(("Ceph Toolbox:", f"kubectl describe pod {pod_names[0]} -n {ns} | grep 'Conditions:' -A 6"))
                page.append(("Ceph Status Logs:", ['kubectl', 'logs', '-n', ns, pod_names[0]]))
                view_page(f'Namespace: {ns}', page)
        # If auto scrolling is enabled, move to a watch nodes loop
        if interval > 0:
            watch_nodes()

def watch_nodes():
    while True:
        nodes = get_nodes()
        for node in nodes:
            page = []
            page.append((f"Pods:", ['kubectl', 'get', 'po', f'--field-selector=spec.nodeName={node}', '-A', '-o', 'wide']))
            page.append(("Allocated Memory:\tRequests\tLimits", f"kubectl describe node {node} | grep 'Allocated' -A 8 | grep 'memory'"))
            page.append(("Allocated CPU:\t\tRequests\tLimits", f"kubectl describe node {node} | grep 'Allocated' -A 8 | grep 'cpu'"))
            page.append(("Labels:", f"kubectl get node {node} -o jsonpath=\"{{.metadata.labels}}\""))
            page.append(("Taints:", f"kubectl get node {node} -o jsonpath=\"{{.spec.taints[*].key}}={{.spec.taints[*].effect}}\""))
            view_page(f'Node: {node}', page)

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
    parser.add_argument('--nodes', '-n', action='store_true', help='begin watching nodes instead of namespaces')
    parser.add_argument('--interval', '-i', type=int, default=5, help='Interval between checks in seconds (default: 5)')
    parser.add_argument('--ask', action='store_true', help='Ask for confirmation before each iteration (default: False)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def main(args):
    args = parse_args()
    global interval
    global do_ask
    global debug
    interval = args.interval
    do_ask = args.ask
    debug = args.debug

    signal.signal(signal.SIGINT, signal_handler)

    # Begin watching
    watch(args.nodes)


if __name__ == "__main__":
    main(sys.argv[1:])