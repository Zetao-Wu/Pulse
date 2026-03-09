import threading, signal, sys, os, time
from logger import log
from scanner import run_scanner
from api import run_api



shutdown_flag = threading.Event()

def handle_shutdown(signum, frame):
    log("INFO", "Shutdown Signal Recieved", signum=signum, frame=frame)
    shutdown_flag.set()


if __name__ == "__main__":    
    pid = os.getpid()
    log("INFO", "Pulse Starting", pid=pid)
    
    initial_res = {
        "processes": [],
        "last_scan": None,
        "scan_count": 0,
        "total_procs": 0,
        "alerts": [],
    }

    # one for sigterm, one for sigint
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    scanner = threading.Thread(
        target=run_scanner,
        args=(initial_res, shutdown_flag),
        daemon=True
    )
    scanner.start()

    api_thread = threading.Thread(
        target=run_api,
        args=(initial_res, shutdown_flag),
        daemon=True
    )

    api_thread.start()
    
    while not shutdown_flag.is_set():
        time.sleep(1)
    log("INFO", "Pulse Stopping")
    scanner.join(timeout=5)
    api_thread.join(timeout=5)
    log("INFO", "Pulse Stopped Cleanly")




    