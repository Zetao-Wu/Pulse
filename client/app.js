const API = "http://localhost:9000"

// ── Update metric cards ──────────────────────────────────────────
async function loadMetrics() {
    try {
        const res  = await fetch(API + "/metrics")
        const data = await res.json()

        document.getElementById("total-procs").textContent = data.total_procs
        document.getElementById("alert-count").textContent = data.alert_count
        document.getElementById("scan-count").textContent  = data.scan_count
        document.getElementById("last-scan").textContent   = data.last_scan
            ? new Date(data.last_scan).toLocaleTimeString()
            : "--"

        document.getElementById("last-updated").textContent =
            "Last updated: " + new Date().toLocaleTimeString()

    } catch (e) {
        console.error("Failed to load metrics", e)
    }
}

// ── Update alerts panel ──────────────────────────────────────────
async function loadAlerts() {
    try {
        const res     = await fetch(API + "/alerts")
        const data    = await res.json()
        const container = document.getElementById("alerts-container")

        if (data.alerts.length === 0) {
            container.innerHTML = '<p class="no-alerts">No alerts — system healthy</p>'
            return
        }

        container.innerHTML = data.alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-name">⚠ ${alert.name} — PID ${alert.pid} — ${alert.reason}</div>
                <div class="alert-details">${alert.details}</div>
            </div>
        `).join("")

    } catch (e) {
        console.error("Failed to load alerts", e)
    }
}

// ── Update process table ─────────────────────────────────────────
async function loadProcesses() {
    try {
        const res  = await fetch(API + "/processes")
        const data = await res.json()
        const tbody = document.getElementById("process-table-body")

        // show top 50 processes sorted by cpu
        const top50 = data.processes.slice(0, 50)

        tbody.innerHTML = top50.map(p => `
            <tr>
                <td title="${p.name}">${p.name.split("/").pop()}</td>
                <td>${p.pid}</td>
                <td>${p.cpu_percent.toFixed(1)}</td>
                <td>${p.memory_mb}</td>
                <td>${p.threads}</td>
                <td>${p.open_fds}</td>
            </tr>
        `).join("")

    } catch (e) {
        console.error("Failed to load processes", e)
    }
}

// ── Refresh everything ───────────────────────────────────────────
async function refresh() {
    await loadMetrics()
    await loadAlerts()
    await loadProcesses()
}

// Run immediately then every 3 seconds
refresh()
setInterval(refresh, 3000)
