#!/opt/homebrew/bin/python3
import os
import time
import subprocess
import signal
import sys

class VM:
    def __init__(self, name):
        self.name = name

    def getTime(self):
        #return subprocess.check_output(['limactl', 'shell', self.name, 'timedatectl']).decode('utf-8').strip()
        try: 
            result = subprocess.check_output(['limactl', 'shell', self.name, 'timedatectl', 'status']).decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            print(f'Error getting time for {self.name}: {e}')
            return ''
        
        return result
    
    def restart(self):
        # give some time in case the VM is in the process of shutting down
        time.sleep(5)
        if self.isVm():
            try:
                subprocess.run(['limactl', 'stop', self.name])
                time.sleep(1)
                subprocess.run(['limactl', 'start', self.name])
            except subprocess.CalledProcessError as e:
                print(f'Error restarting {self.name}: {e}')
        else:
            print(f'{self.name} is not a VM')

    def isSystemClockSynced(self):
        result = self.getTime()
        for line in result.split('\n'):
            if 'System clock synchronized' in line:
                return 'yes' in line
    
    def isVm(self):
        vms = VM.getVMs()
        return self.name in [vm.name for vm in vms]

    def getVMs():
        try:
            result = subprocess.check_output(['limactl', 'list', '--format', '{{.Name}}']).decode('utf-8').split('\n')
        except subprocess.CalledProcessError as e:
            print(f'Error getting VMs: {e}')
            return []

        return [VM(vm) for vm in result if vm != '']

    def printLogs(self):
        try:
            #with open(f'/Users/mtyler/Workspace/kwatch/{self.name}_{time.strftime("%H%M%S")}_dmesg.log', 'w') as log_file:
            #    log_file.write(subprocess.check_output(['limactl', 'shell', self.name, 'sudo', 'dmesg']).decode('utf-8').strip())
            log_dir = f'/Users/mtyler/Workspace/kwatch/logs_{time.strftime("%m%d%Y")}'
            os.makedirs(log_dir, exist_ok=True)
            with open(f'{log_dir}/{self.name}_{time.strftime("%H%M%S")}_chrony.log', 'w') as log_file:
                log_file.write(subprocess.check_output(['limactl', 'shell', self.name, 'sudo', 'journalctl', '-u', 'chrony']).decode('utf-8').strip())
                log_file.write(subprocess.check_output(['limactl', 'shell', self.name, 'sudo', 'chronyc', 'sources']).decode('utf-8').strip())
                log_file.write(subprocess.check_output(['limactl', 'shell', self.name, 'sudo', 'chronyc', 'sourcestats']).decode('utf-8').strip())
                log_file.write(subprocess.check_output(['limactl', 'shell', self.name, 'sudo', 'chronyc', '-n', 'tracking']).decode('utf-8').strip())
            #print(subprocess.check_output(['limactl', 'shell', self.name, 'sudo', 'dmesg']).decode('utf-8').strip())
        except subprocess.CalledProcessError as e:
            print(f'Error getting logs for {self.name}: {e}')

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
        vms = VM.getVMs()
        for vm in vms:
            if not vm.isSystemClockSynced():
                print(f'{vm.name} is not synced @ {time.ctime()}')
                vm.printLogs()
                vm.restart()
                #vm.printLogs()
#                print(f'{vm.name} is not synced')
#                subprocess.run(['limactl', 'stop', vm.name])
#                subprocess.run(['limactl', 'start', vm.name])
        print('.')
        time.sleep(20)

if __name__ == "__main__":
    main(sys.argv)