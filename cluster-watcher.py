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

    def add_command(self, command):
        self.commands.append(command)

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
        if cmd == 'f':
            self.refresh()
        elif cmd == 'd':
            watch_nodes()
        elif cmd == 's':
            watch_ns()
        elif cmd == 'a':
            exec_checks()

def rest():
    cmd = ''
    if do_ask:
        cmd = input("\nCtrl+c exit | a=checks | s=ns | d=nodes | f=refresh:")
    else:
        time.sleep(interval)
    return cmd


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
        # Get all namespaces and return details for each        
        namespaces = get_namespaces()
        for ns in namespaces:
            # Begin Page 1 for each namespace
            page = []
            page.append(("Pods:", ['kubectl', 'get', 'po', '-n', ns, '-o', 'wide']))
            page.append(("Services:", ['kubectl', 'get', 'svc', '-n', ns, '-o', 'wide']))
            page.append(("Events:", ['kubectl', 'events', '-n', ns, '--types=Warning']))
            ## Uncomment to display deployments and services
            ##   page.append(("Deployments:", ['kubectl', 'get', 'deploy', '-n', ns, '-o', 'wide']))
            ##   page.append(("Services:", ['kubectl', 'get', 'svc', '-n', ns, '-o', 'wide']))
            view_page(f"Namespace: {ns}", page)

        # If auto scrolling is enabled, move to a watch nodes loop
        if not do_ask:
            watch_nodes()

def watch_nodes():
    while True:
        ## Show cluster overview
        page = []
        page.append(("Cluster Info:", ['kubectl', 'cluster-info']))
        page.append(("Nodes:", ['kubectl', 'get', 'no', '-o', 'wide']))
        page.append(("Conditions:", ['kubectl', 'get', 'no', '-o', 'jsonpath={range .items[*]}{.metadata.name}{": "}{range .status.conditions[*]}{.type}{"="}{.status}{" "}{end}{"\\n"}{end}']))
        page.append(("Storage Classes:", ['kubectl', 'get', 'sc', '-o', 'wide']))
        page.append(("Persistent Volumes:", ['kubectl', 'get', 'pv', '-o', 'wide']))
        page.append(("Events:", ['kubectl', 'events', '--types=Warning', '-A']))
            ## Uncomment to display allocated resources as displayed in the node status object
        ## not very helpful...
        #page.append(("Allocated Resources:", ['kubectl', 'get', 'no', '-o', 'jsonpath={range .items[*]}{.metadata.name}{": cpu "}{.status.allocatable.cpu}{" mem "}{.status.allocatable.memory}{" eph-storage "}{.status.allocatable.ephemeral-storage}{"\\n"}{end}']))
        view_page('Cluster Overview', page)

        ## Show allocated resources of all nodes in one page
        page = []
        nodes = get_nodes()
        page.append(("Allocated:\tRequests\tLimits", ""))
        for node in nodes:
            page.append(("", f"echo {node} $(kubectl describe node {node} | grep 'Allocated' -A 8 | grep 'memory' | xargs)"))

        for node in nodes:
            page.append(("", f"echo {node} $(kubectl describe node {node} | grep 'Allocated' -A 8 | grep 'cpu' | xargs)"))
        
        view_page(f'Allocated Resources:', page)

        ## Show node details
        nodes = get_nodes()
        for node in nodes:
            page = []
            page.append((f"Pods:", ['kubectl', 'get', 'po', f'--field-selector=spec.nodeName={node}', '-A', '-o', 'wide']))
            #page.append(("Allocated Memory:\tRequests\tLimits", f"kubectl describe node {node} | grep 'Allocated' -A 8 | grep 'memory'"))
            #page.append(("Allocated CPU:\t\tRequests\tLimits", f"kubectl describe node {node} | grep 'Allocated' -A 8 | grep 'cpu'"))
            page.append(("Labels:", f"kubectl get node {node} -o jsonpath=\"{{.metadata.labels}}\""))
            page.append(("Taints:", f"kubectl get node {node} -o jsonpath=\"{{range .spec.taints[*]}}{{.key}}={{.effect}} {{end}}\""))
            view_page(f'Node: {node}', page)


        # If auto scrolling is enabled, move to a watch namespaces loop
        if not do_ask:
            watch_ns()

def exec_checks():
    checks = [
        # A list of "critical" services/resources to validate that cluster is operational
        # Checks for kube-system components for errors
        #('Control Plane System Time:', 'limactl shell cp1 timedatectl | grep time: | grep -E "Local|Universal"'),
        ('Control Plane System Time:', 'echo "lima-cp1"; limactl shell cp1 timedatectl; echo "lima-n1"; limactl shell n1 timedatectl; echo "lima-n2"; limactl shell n2 timedatectl; echo "lima-n3"; limactl shell n3 timedatectl;'),
        ('kube-system - kubeadm-config', 'kubectl get configmaps -n kube-system kubeadm-config -o yaml'),
        ('kube-system - kube-apiserver - err logs:', 'kubectl logs -n kube-system -l component=kube-apiserver --tail=20 | grep err'),
        ('kube-system - kube-controller-manager - err logs:', 'kubectl logs -n kube-system -l component=kube-controller-manager --tail=20 | grep err'),
        ('kube-system - kube-scheduler - err logs:', 'kubectl logs -n kube-system -l component=kube-scheduler --tail=20 | grep err'),
        ('kube-system - kube-proxy - err logs:', 'kubectl logs -n kube-system -l k8s-app=kube-proxy --tail=20 | grep err'),
        # check bootstrap
        ('cert-manager - Logs:', 'kubectl logs -n cert-manager -l app.kubernetes.io/instance=cert-manager --tail=20 | grep err'),
        ('cert-manager - Cluster Issuer:', 'kubectl describe clusterissuers.cert-manager.io'),
        ('cert-manager - CertSignReqs:', 'kubectl get csr -A'),
        # check argocd
        ('argocd - argocd-server - logs:', 'kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server --tail=20'),
        # check rook
        ('rook-ceph - status:', ['kubectl', 'rook-ceph', 'ceph', 'status']),
        # Checks for monitoring
        # uncomment to check prometheus-operator
        #('monitoring - prometheus-operator - all logs:', 'kubectl logs -n monitoring -l app.kubernetes.io/component=prometheus-operator --tail=20'),
        #('monitoring - service monitors - all:', 'kubectl get servicemonitors.monitoring.coreos.com -A'),
        #('monitoring - operator - init-config logs:', 'kubectl -n monitoring logs prometheus-prometheus-kube-prometheus-prometheus-0 init-config-reloader'),
        #('monitoring - operator - config logs:', 'kubectl -n monitoring logs prometheus-prometheus-kube-prometheus-prometheus-0 config-reloader'),
        #('monitoring - operator - prometheus logs:', 'kubectl -n monitoring logs prometheus-prometheus-kube-prometheus-prometheus-0 prometheus'),
        #('monitoring - operator - kubectl exec -n monitoring -it prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- cat /etc/prometheus/config_out/prometheus.env.yaml:', 
        # 'kubectl exec -n monitoring -it prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- cat /etc/prometheus/config_out/prometheus.env.yaml | grep "serviceMonitor"'),
        # Checks for Network
        ## check ingress
        #('ingress-nginx - ingress-nginx-controller - logs:', 'kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=20 | grep err'),
        # check flannel
        ('kube-flannel - kube-flannel - logs:', 'kubectl logs -n kube-flannel -l k8s-app=flannel -c kube-flannel --tail=20 | grep err'),
        #('gateway:' , ['kubectl', 'logs', '-n', 'gateway', '-l', 'app.kubernetes.io/name=nginx-gateway-fabric', '-c', 'init' '--tail=20']),
        #('metrics-server:', 'kubectl logs -n kube-system -l app.kubernetes.io/name=metrics-server --tail=20 | grep err'),
        ##### Helpful but not critical            
##            # Begin Page 3 for each namespace
##            if ns == 'rook-ceph':
##                page = []
##                pod_names = get_pod_by_label(ns,'app=rook-ceph-tools') ### app=rook-ceph-tools-operator-image
##                page.append(("Ceph Toolbox Pod:", f"kubectl describe pod {pod_names[0]} -n {ns} | grep 'Conditions:' -A 6"))
##                page.append(("Ceph Status Logs:", ['kubectl', 'logs', '-n', ns, pod_names[0]]))
##                view_page(f'Namespace: {ns} 3', page)
##            elif ns == 'dashboard':
##                page = []
##                pod_names = get_pod_by_label(ns,'app.kubernetes.io/instance=kubernetes-dashboard')
##                page.append(("Dashboard Pod:", f"kubectl describe pod {pod_names[0]} -n {ns} | grep 'Conditions:' -A 6"))
##                view_page(f'Namespace: {ns} 3', page)
            #elif ns == 'cert-manager':
            #    page.append(("Logs:", ['kubectl', 'logs', '-n', ns, '-l', "app.kubernetes.io/instance=cert-manager", '--tail=5']))

    ]
    for check in checks:
        index = checks.index(check)
        sc_page = []
        sc_page.append(check)
        view_page(f'System Check {index + 1}/{len(checks)}:', sc_page)

    # return to namespace watch loop
    watch_ns()



    
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