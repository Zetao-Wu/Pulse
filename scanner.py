import subprocess
from logger import log
from datetime import datetime, timezone
from detectors import check_anomalies, check_fd_leaks


def get_all_fd_counts():
    """
    Run lsof once for all processes.
    """
    try:
        res = subprocess.run(
            ["lsof", "-n", "-P"],
            capture_output=True,
            text=True
        )

        counts = {}
        for line in res.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1])
                counts[pid] = counts.get(pid, 0) + 1
            except:
                continue
        return counts
    except:
        return {}


def read_process(pid, fd_counts):
    """
    Read a single process given the PID and ask the OS for everything required:
        - Name
        - CPU
        - Memory
        - Threads
        - File Descriptors
    Return as dictionary, if process died return None
    """

    try:
        # process_anme
        res_process_name = subprocess.run(
            ["ps", "-p", str(pid), "-o", "comm="],
            capture_output=True,
            text=True
        )

        if res_process_name.returncode != 0:
            return None
        
        name = res_process_name.stdout.strip()

        res_memory_cpu = subprocess.run(
            ["ps", "-p", str(pid), "-o","rss=,%cpu="],
            capture_output=True,
            text=True
        )

        if res_memory_cpu.returncode != 0:
            return None
        
        memory_cpu = res_memory_cpu.stdout.strip()
        parts = memory_cpu.split()
        memory_mb = round(int(parts[0]) / 1024, 2)
        cpu_percent = float(parts[1])

        open_fds = fd_counts.get(pid, 0)

        res_threads = subprocess.run(
            ["ps", "-p", str(pid), "-M"],
            capture_output=True,
            text=True
        )

        
        thread_lines = [l for l in res_threads.stdout.splitlines() if l.strip()]
        threads = max(0, len(thread_lines) - 1)

        return {
            "pid": pid,
            "name": name,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "threads": threads,
            "open_fds": open_fds
        }

    except:
        return None


def get_all_pids():
    try:
        res_pids = subprocess.run(
            ["ps", "ax", "-o", "pid="],
            capture_output=True,
            text=True
        )

        pid_line = [int(p.strip()) for p in res_pids.stdout.splitlines() if p.strip()]
        return pid_line

    except:
        return []



def run_scanner(results_store, shutdown_flag):
    """
    Scan all processes to get every PID on the machine. For each PID call  `read_process`
    Collect all results, store them, wait 3 seconds, repeat until shutdown.
    """
    log("INFO", "Scanner Started", interval=3)

    scan_count = 0

    while not shutdown_flag.is_set():
        begin_time = datetime.now(timezone.utc)
        scan_count += 1

        pids = get_all_pids()
        fd_counts = get_all_fd_counts()

        processes = []

        for pid in pids:
            info = read_process(pid, fd_counts)
            if info is None:
                continue
            processes.append(info)

        processes = sorted(processes, key=lambda item: item['cpu_percent'], reverse=True)
        
        results_store["processes"]   = processes
        results_store["last_scan"]   = datetime.now(timezone.utc).isoformat()
        results_store["scan_count"]  = scan_count
        results_store["total_procs"] = len(processes)

        alerts = check_anomalies(processes) + check_fd_leaks(processes)
        results_store["alerts"] = alerts
        if alerts:
            log("WARN", "Anomalies Detected", count=len(alerts))
            for alert in alerts:
                log("WARN", alert["reason"], pid=alert["pid"], name=alert["name"], details=alert["details"])

        duration = round((datetime.now(timezone.utc) - begin_time).total_seconds(), 3)

        log("INFO", "Scanner Completed", scan=scan_count, processes=len(processes), duration_s=duration)

        shutdown_flag.wait(timeout=3)

    log("INFO", "Scanner Stopped")
