from logger import log

CPU_THRESHOLDS = 80.0 #percent
MEMORY_THRESHOLD = 2048.0 #MB
FD_GROWTH_SCANS = 4 #how many consecutive growing scans = potential leak

fd_history = {} # persist memory across scans

def check_anomalies(processes):
    """
    Looks at every process right now
        If CPU is too high => Alert
        If memory is too high => Alert
    Return a list of alerts
    """
    
    log("INFO", "Checking Anomalies")
    alerts = []

    for process in processes:
        cpu_percent = process["cpu_percent"]
        memory_mb = process["memory_mb"]
        if cpu_percent > CPU_THRESHOLDS:
            alerts.append(
                {
                    "pid": process["pid"],
                    "name": process["name"],
                    "severity": "WARN",
                    "reason": "CPU Spike",
                    "details": f"cpu={cpu_percent}"
                }
            )
        if memory_mb > MEMORY_THRESHOLD:
            alerts.append(
                {
                    "pid": process["pid"],
                    "name": process["name"],
                    "severity": "WARN",
                    "reason": "Memory Spike",
                    "details": f"memory_mb={memory_mb}"
                }
            )
    return alerts


def check_fd_leaks(processes):
    """
    Look at every process's FD count right now
        Compare it to previous scans
        If FDs keep growing scan after scan => alert
    Return a list of alerts
    """
    log("INFO", "Checking for FD Leaks")
    alerts = []

    for process in processes:
        if process["pid"] not in fd_history:
            fd_history[process["pid"]] = []
        curr_entry = fd_history[process["pid"]]
        curr_entry.append(process["open_fds"])
        fd_history[process["pid"]] = curr_entry[-5:]
        if len(curr_entry) > 4:
            last_five = curr_entry[-5:]
            alert = True
            for i in range(0,4):
                if last_five[i] >= last_five[i + 1]:
                    alert = False
                    break
            if alert == True:
                alerts.append(
                    {
                        "pid": process["pid"],
                        "name": process["name"],
                        "severity": "WARN",
                        "reason": "Possible FD Leak",
                        "details": f"Last five open FD count: {last_five}"
                    }
            )
    return alerts