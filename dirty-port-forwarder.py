#!/opt/homebrew/bin/python3
import argparse
import multiprocessing
import os
import signal
import subprocess
import sys
import time

forward_services = {
  #svc_name: { namespace: target_port: host_port: extra_args: }
  "argocd-server": {
    "namespace": "argocd",
    "target_port": 443,
    "host_port": 8080,
    "extra_args": "--address 0.0.0.0"
  },
  "prometheus-grafana": {
    "namespace": "monitoring",
    "target_port": 80,
    "host_port": 8081
  },
  "prometheus-kube-prometheus-prometheus": {
    "namespace": "monitoring",
    "target_port": 9090,
    "host_port": 8082
  },
  "alertmanager-operated": {
    "namespace": "monitoring",
    "target_port": 9093,
    "host_port": 8083
  },
  "rook-ceph-mgr-dashboard": {
    "namespace": "rook-ceph",
    "target_port": 7000,
    "host_port": 8084
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

def run_kubectl():
    while True:
        try:
            subprocess.run(['kubectl', 'get', 'events', '-A'], check=True)
            return True
        except subprocess.CalledProcessError:
            print("kubectl command failed, we'll try agin in a few...")
            time.sleep(5)  # Wait for a second before restarting

def signal_handler(sig, frame):
    print("Received SIGINT, exiting...")
    for process in multiprocessing.active_children():
      print(f"Terminating process with PID: {process.pid}")
      process.terminate()
    sys.exit(0)

def parse_args():
    parser = argparse.ArgumentParser(description='Watch all pods in all namespaces.')
    parser.add_argument('--ingress', '-i', action='store_true', help='Watch ingress pods')
    return parser.parse_args()

def main(args):
    args = parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    if run_kubectl():
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

if __name__ == "__main__":
    main(sys.argv)