#!/opt/homebrew/bin/python3

import subprocess
import time

def run_kubectl_logs():
    while True:
        try:
            subprocess.run(
                ['kubectl', 'logs', '-n', 'gateway', '-l', 'app.kubernetes.io/name=nginx-gateway-fabric', '-c', 'nginx', '-f'],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"kubectl logs command failed with error: {e}. Restarting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    run_kubectl_logs()