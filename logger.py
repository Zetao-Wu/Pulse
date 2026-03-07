from datetime import datetime, timezone

# store the last 100 log entries in memory
# other parts of system will read from this list

log_entries = []

def log(level, message, **context):
    # get current timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        **context
    }

    log_entries.append(entry)
    if len(log_entries) > 100:
        log_entries.pop(0)

    context_str = "  ".join(f"{k}={v}" for k, v in context.items())

    print(f"[{level}] {timestamp} - {message}   {context_str}")


if __name__ == "__main__":
    log("INFO", "Scanner Started", interval=3, pid=2134)
    log("WARN", "Anomaly Detected", pid=5678, reason="CPU Spike")
    log("ERROR", "Failed to Read Process", pid=999, error="Permission Denied")

    print("\\n--- Stored Entries ---")
    for entry in log_entries:
        print(entry)