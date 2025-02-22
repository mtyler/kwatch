#!/opt/homebrew/bin/python3
import argparse
import os
import time
import subprocess
import signal
import sys

class VM:
    def __init__(self, name):
        self.name = name

    def getTime(self):
        return subprocess.check_output(['limactl', 'shell', self.name, 'timedatectl']).decode('utf-8').strip()
    
    def isSystemClockSynced(vm):
        result = vm.getTime()
        for line in result.split('\n'):
            if 'System clock synchronized' in line:
                return 'yes' in line     

    def getVMs():
        result = subprocess.check_output(['limactl', 'list', '--format', '{{.Name}}']).decode('utf-8').split('\n')
        return [VM(vm) for vm in result if vm != '']

    def printLogs(vm):
        print(subprocess.check_output(['limactl', 'shell', vm.name, 'sudo', 'dmesg']).decode('utf-8').strip())

def signal_handler(sig, frame): 
    sys.exit(0)


def main(args):
    signal.signal(signal.SIGINT, signal_handler)
    vms = VM.getVMs()
    print(f'Clock synchronization watcher started. Found {len(vms)} VMs')

    if len(vms) == 0:
        print('No VMs found. Exiting.')
        sys.exit(1)

    while True:
        for vm in vms:
            if not VM.isSystemClockSynced(vm):
                vm.printLogs(vm)
#                print(f'{vm.name} is not synced')
#                subprocess.run(['limactl', 'stop', vm.name])
#                subprocess.run(['limactl', 'start', vm.name])
        print('.')
        time.sleep(60)

if __name__ == "__main__":
    main(sys.argv[1:])