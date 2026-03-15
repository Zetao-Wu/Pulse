import json, socket, threading
from logger import log
from auth import validate_req
from datetime import datetime, timezone
from detectors import check_anomalies, check_fd_leaks
from storage import save_scan

PORT = 9000

def handle_request(client_socket, results_store):
    try:
        raw = b""
        client_socket.settimeout(10.0)
        try:
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                raw += chunk

                if b"\r\n\r\n" in raw:
                    header_part = raw.split(b"\r\n\r\n")[0]
                    body_part = raw.split(b"\r\n\r\n", 1)[1]
                    content_length = 0
                    for line in header_part.split(b"\r\n"):
                        if line.lower().startswith(b"content-length:"):
                            content_length = int(line.split(b":")[1].strip())
                            break
                    if content_length == 0 or len(body_part) >= content_length:
                        break
        except Exception:
            pass

        raw_req = raw.decode("utf-8")

        valid, status_code, message = validate_req(raw_req)

        if not valid:
            body_str = json.dumps({"error": message})

            response = (
                "HTTP/1.1 " + str(status_code) + "\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Content-Length: " + str(len(body_str)) + "\r\n"
                "\r\n" +
                body_str
            )
            client_socket.sendall(response.encode("utf-8"))
            return

        first_line = raw_req.split("\r\n")[0]

        parts = first_line.split(" ")
        path = parts[1] if len(parts) > 1 else "/"
        method = parts[0] if len(parts) > 0 else "GET"


        if method == "OPTIONS":
            response = (
                "HTTP/1.1 204 No Content\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                "Access-Control-Allow-Headers: X-API-Key, Content-Type\r\n"
                "\r\n"
            )
            client_socket.sendall(response.encode("utf-8"))
            return
        

        if path == "/health":
            status = "200 OK"
            body = {
                "status": "ok",
                "scan_count": results_store["scan_count"],
                "last_scan": results_store["last_scan"]
            }
        elif path == "/processes":
            status = "200 OK"
            body = {
                "processes": results_store["processes"],
                "total": results_store["total_procs"]
            }
        elif path == "/alerts":
            status = "200 OK"
            body = {
                "alerts": results_store["alerts"],
                "total": len(results_store["alerts"])
            }
        elif path == "/metrics":
            status = "200 OK"
            body = {
                "total_procs": results_store["total_procs"],
                "scan_count":  results_store["scan_count"],
                "last_scan":   results_store["last_scan"],
                "alert_count": len(results_store["alerts"])
            }
        elif path == "/ingest" and method == "POST":
            try:
                body = raw_req.split("\r\n\r\n", 1)[1]
                payload = json.loads(body)
                hostname = payload.get("hostname", "unknown")
                processes = payload.get("processes", [])
                results_store["processes"] = processes
                results_store["last_scan"] = datetime.now(timezone.utc).isoformat()
                results_store["scan_count"] += 1
                alerts = check_anomalies(processes) + check_fd_leaks(processes)
                results_store["alerts"] = alerts
                save_scan(processes, alerts, hostname)
                status = "200 OK"
                body = {
                    "status": "ok",
                    "received": len(processes)
                }
            except Exception as e:
                status = "500 Internal Server Error"
                body   = {"error": str(e)}
        else:
            status = "404 Not Found"
            body = {"error": "not found"}

        body_str = json.dumps(body)

        response = (
            "HTTP/1.1 " + status + "\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Content-Length: " + str(len(body_str)) + "\r\n"
            "\r\n" +
            body_str
        )

        client_socket.sendall(response.encode("utf-8"))

    except Exception as e:
        log("ERROR", "Failed to handle request", error=str(e))
    finally:
        client_socket.close()


def run_api(results_store, shutdown_flag):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", PORT))
    server.listen(5)
    server.settimeout(1.0)

    log("INFO", "API Started", port=PORT)

    while not shutdown_flag.is_set():
        try:
            client_socket, address = server.accept()
            log("INFO", "Connection accepted", address=str(address))
            thread = threading.Thread(
                target=handle_request,
                args=(client_socket, results_store),
                daemon=True
            )
            thread.start()
        except socket.timeout:
            continue

    server.close()
    log("INFO", "API Stopped")


if __name__ == "__main__":
    shutdown_flag = threading.Event()
    results_store = {
        "processes": [],
        "alerts": [],
        "last_scan": None,
        "scan_count": 0,
        "total_procs": 0
    }
    run_api(results_store, shutdown_flag)
