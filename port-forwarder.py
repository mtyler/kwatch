#!/opt/homebrew/bin/python3
import argparse
import multiprocessing
import os
import signal
import subprocess
import sys
import time

forward_services = {
    #svc_name: namespace: target_port: host_port:
  "prometheus-grafana": {
    "namespace": "monitoring",
    "target_port": 80,
    "host_port": 2000
  },
  "alertmanager-operated": {
    "namespace": "monitoring",
    "target_port": 9093,
    "host_port": 2001
  },
  "prometheus-kube-prometheus-prometheus": {
    "namespace": "monitoring",
    "target_port": 9090,
    "host_port": 2002
  },
  "rook-ceph-mgr-dashboard": {
    "namespace": "rook-ceph",
    "target_port": 7000,
    "host_port": 2003
  },
  "kubernetes-dashboard-kong-proxy": {
    "namespace": "dashboard",
    "target_port": 80,
    "host_port": 2004
  }
}

kinfra_ingress = {
    "ingress-nginx-controller": {
        "namespace": "ingress-nginx",
        "target_port": 80,
        "host_port": 80,
        "extra_args": "--address=0.0.0.0"
    },
    "ingress-nginx-controller": {
        "namespace": "ingress-nginx",
        "target_port": 443,
        "host_port": 443,
        "extra_args": "--address=0.0.0.0"
    }
}

def process_task(task):
    process = subprocess.Popen(task, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ, shell=True)
    print(f"Started process: {task} with PID: {process.pid}")
    stdout, stderr = process.communicate()
    return stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip()

def get_tasks(svc):
    tasks = []
    for svc_name, details in svc.items():
        namespace = details["namespace"]
        target_port = details["target_port"]
        host_port = details["host_port"]
        extra_args = details.get("extra_args", "")
        tasks.append(f"kubectl port-forward -n {namespace} svc/{svc_name} {host_port}:{target_port} {extra_args}")
        # used to pass the command as a list of strings
        #tasks.append(['kubectl','port-forward','-n', namespace, f'svc/{svc_name}', f'{host_port}:{target_port}'])
    return tasks


def signal_handler(sig, frame):
    print("Received SIGINT, exiting...")
    sys.exit(0)

def parse_args():
    parser = argparse.ArgumentParser(description='Watch all pods in all namespaces.')
    parser.add_argument('--ingress', '-i', action='store_true', help='Watch ingress pods')
    return parser.parse_args()

def main(args):
    args = parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    if args.ingress:
        tasks = get_tasks(kinfra_ingress)
    else:
        # List of tasks/cmds to perform and watch
        tasks = get_tasks(forward_services)

    with multiprocessing.Pool(processes=len(tasks)) as pool:
        results = pool.map(process_task, tasks)
        while True:
            for stdout, stderr in results:
                if stdout != "":
                  print(stdout)
                if stderr != "":
                  print(stderr)

            time.sleep(1)
       

#    for result in results:
#        print(result.stdout.read().decode())
#        print(result.stderr.read().decode())

if __name__ == "__main__":
    main(sys.argv)