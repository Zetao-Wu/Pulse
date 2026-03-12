import sqlite3

def init_db():
    """
    1. connect to pulse.db
    2. create processes table if not exists
    3. create alerts table if not exists
    4. create indexes on pid and scanned_at
    5. commit and close
    """

    conn = sqlite3.connect("pulse.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pid         INTEGER,
            name        TEXT,
            cpu         REAL,
            memory_mb   REAL,
            threads     INTEGER,
            open_fds    INTEGER,
            scanned_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pid         INTEGER,
            name        TEXT,
            severity    TEXT,
            reason      TEXT,
            details     TEXT,
            fired_at    TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pid ON processes (pid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scanned_at ON processes (scanned_at)")

    conn.commit()
    conn.close()

def save_scan(processes, alerts):
    """
    1. connect to pulse.db
    2. for each process in processes list:
        insert a row into processes table
    3. for each alert in alerts list:
        insert a row into alerts table
    4. commit
    5. close
    """

    conn = sqlite3.connect("pulse.db")
    cursor = conn.cursor()

    for p in processes:
        cursor.execute("""
            INSERT INTO processes(pid, name, cpu, memory_mb, threads, open_fds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (p["pid"], p["name"], p["cpu_percent"], p["memory_mb"], p["threads"], p["open_fds"]))

    for a in alerts:
        cursor.execute("""
            INSERT INTO alerts(pid, name, severity, reason, details)
            VALUES (?, ?, ?, ?, ?)
        """, (a["pid"], a["name"], a["severity"], a["reason"], a["details"]))
    
    conn.commit()
    conn.close()

def get_recent_processes(limit=50):
    """
    connect to pulse.db
    SELECT most recent scan's processes
    ORDER BY scanned_at DESC
    LIMIT limit
    return as list of dicts
    close
    """
    conn = sqlite3.connect("pulse.db")
    cursor = conn.cursor()
    res = []

    cursor.execute("""
    SELECT * FROM processes
    ORDER BY scanned_at DESC
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    for row in rows:
        res.append({
            "pid": row[1],
            "name": row[2],
            "cpu_percent": row[3],
            "memory_mb": row[4],
            "threads": row[5],
            "open_fds": row[6],
            "scanned_at": row[7],
        })

    conn.close()
    return res



def get_recent_alerts(limit=100):
    """
    connect to pulse.db
    SELECT most recent alerts
    ORDER BY fired_at DESC
    LIMIT limit
    return as list of dicts
    close
    """
    conn = sqlite3.connect("pulse.db")
    cursor = conn.cursor()

    res = []

    cursor.execute("""
    SELECT * FROM alerts
    ORDER BY fired_at DESC
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    for row in rows:
        res.append({
            "pid": row[1],
            "name": row[2],
            "severity": row[3],
            "reason": row[4],
            "details": row[5],
            "fired_at": row[6],
        })
    
    conn.close()
    return res


def cleanup_old_data():
    """
    connect to pulse.db
    DELETE FROM processes WHERE scanned_at is older than 24 hours
    DELETE FROM alerts WHERE fired_at is older than 24 hours
    commit
    close
    """
    conn = sqlite3.connect("pulse.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM processes WHERE scanned_at < datetime('now', '-24 hours')")
    cursor.execute("DELETE FROM alerts WHERE fired_at < datetime('now', '-24 hours')")
    conn.commit()

    conn.close()