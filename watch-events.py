#!/opt/homebrew/bin/python3
import signal
import subprocess
import sys
import time

def run_kubectl():
    while True:
        try:
            subprocess.run(['kubectl', 'get', 'events', '-A', '-w'], check=True)
        except subprocess.CalledProcessError:
            print("kubectl command failed, we'll try agin in a few...")
            time.sleep(5)  # Wait for a second before restarting

def signal_handler(sig, frame): 
    sys.exit(0)
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    run_kubectl()