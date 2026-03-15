import socket
import json
import time
import threading
import urllib.request
import os

from scanner import get_all_pids, get_all_fd_counts, read_process
from logger import log


PULSE_SERVER = os.environ.get("PULSE_SERVER", "http://localhost:9000")

def get_hostname():
    return socket.gethostname()


def scan_processes():
    res = []
    all_pids = get_all_pids()
    fd_counts = get_all_fd_counts()
    for pid in all_pids:
        info = read_process(pid, fd_counts)
        if info is None:
            continue
        res.append(info)
    return res

def ship_data(hostname, processes, server_url, api_key):
    payload = {
        "hostname": hostname,
        "processes": processes,
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        server_url + "/ingest",
        data=data,
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST"
    )

    try:
        urllib.request.urlopen(req, timeout=5)
        log("INFO", "Data Shipped", hostname=hostname, processes=len(processes))
    except Exception as e:
        log("WARN", "Failed to ship data", error=str(e))



def run_agent(server_url, api_key, shutdown_flag):
    hostname = get_hostname()
    log("INFO", "Agent is running", hostname=hostname, server=server_url)

    while not shutdown_flag.is_set():
        processes = scan_processes()
        ship_data(hostname, processes, server_url, api_key)
        shutdown_flag.wait(timeout=3)

    log("INFO", "Agent Stopped")


if __name__ == "__main__":
    import signal

    api_key = os.environ.get("PULSE_API_KEY", "dev-key-123")
    shutdown_flag = threading.Event()

    def handle_shutdown(signum, frame):
        shutdown_flag.set()

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    run_agent(PULSE_SERVER, api_key, shutdown_flag)