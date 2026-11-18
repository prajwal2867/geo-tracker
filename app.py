
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from http.cookies import SimpleCookie
from urllib.request import Request, urlopen
from urllib.parse import quote, urlsplit
from pathlib import Path
import ipaddress
import json
import shutil
import subprocess
import threading
import secrets
import math


# ==================================================
# CONFIGURATION
# ==================================================

HOST = "0.0.0.0"
PORT = 5000

BASE_DIR = Path(__file__).resolve().parent

SESSION_TIMEOUT = 1800
MAX_REQUEST_SIZE = 16384

# Temporary visitor sessions
visitor_sessions = {}
session_lock = threading.Lock()


# ==================================================
# IP GEOLOCATION
# ==================================================

def get_ip_location(ip_address):

    try:
        ip = ipaddress.ip_address(ip_address)

        # Skip private, reserved and local addresses
        if not ip.is_global:
            return None

        endpoint = (
            f"http://ip-api.com/json/{quote(ip_address, safe='')}"
            "?fields=status,message,city,regionName,country,lat,lon"
        )

        req = Request(
            endpoint,
            headers={
                "User-Agent": "VisitorLocationMonitor/1.0"
            }
        )

        with urlopen(req, timeout=5) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        if data.get("status") != "success":
            return None

        lat = data.get("lat")
        lon = data.get("lon")

        if lat is None or lon is None:
            return None

        city = data.get("city", "Unknown")
        region = data.get("regionName", "Unknown")

        if city != "Unknown":
            accuracy = 25000
            accuracy_level = "CITY-LEVEL ESTIMATE"
        elif region != "Unknown":
            accuracy = 100000
            accuracy_level = "REGION-LEVEL ESTIMATE"
        else:
            accuracy = 250000
            accuracy_level = "COUNTRY-LEVEL ESTIMATE"

        return {
            "latitude": lat,
            "longitude": lon,
            "city": city,
            "region": region,
            "country": data.get("country", "Unknown"),
            "accuracy": accuracy,
            "accuracy_level": accuracy_level,
            "map_link": (
                f"https://www.google.com/maps?q={lat},{lon}"
            )
        }

    except Exception as error:

        print(
            f"[!] IP geolocation lookup failed: {error}",
            flush=True
        )

        return None


# ==================================================
# HTTP REQUEST HANDLER
# ==================================================

class VisitorHandler(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        # Suppress default HTTP access logs
        pass

    # --------------------------------------------------
    # RESPONSE HELPERS
    # --------------------------------------------------

    def send_json(self, data, status=200, extra_headers=None):

        response = json.dumps(data).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        if extra_headers:
            for name, value in extra_headers.items():
                self.send_header(name, value)

        self.end_headers()
        self.wfile.write(response)

    # --------------------------------------------------
    # SESSION HELPERS
    # --------------------------------------------------

    def get_session_id(self):

        cookie = SimpleCookie()

        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            return None

        morsel = cookie.get("visitor_id")

        return morsel.value if morsel else None

    def get_client_ip(self):

        # Cloudflare provides this header when proxied
        cloudflare_ip = self.headers.get("CF-Connecting-IP")

        if cloudflare_ip:
            try:
                return str(
                    ipaddress.ip_address(cloudflare_ip.strip())
                )
            except ValueError:
                pass

        return self.client_address[0]

    # ==================================================
    # GET REQUESTS
    # ==================================================

    def do_GET(self):

        path = urlsplit(self.path).path

        # Serve frontend
        if path == "/":

            index_file = BASE_DIR / "index.html"

            if not index_file.is_file():
                self.send_error(404, "index.html not found")
                return

            content = index_file.read_bytes()

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(content))
            )

            self.end_headers()
            self.wfile.write(content)

            return

        # Track visitor
        if path == "/track":

            self.track_visitor()
            return

        self.send_error(404, "Route not found")

    # --------------------------------------------------
    # VISITOR TRACKING
    # --------------------------------------------------

    def track_visitor(self):

        ip_address = self.get_client_ip()

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Obtain rough IP-based location
        ip_location = get_ip_location(ip_address)

        # Generate a unique visitor session
        session_id = secrets.token_urlsafe(32)

        with session_lock:

            # Remove expired sessions
            current_time = datetime.now().timestamp()

            expired = [
                key for key, value in visitor_sessions.items()
                if current_time - value["created_at"] > SESSION_TIMEOUT
            ]

            for key in expired:
                visitor_sessions.pop(key, None)

            visitor_sessions[session_id] = {
                "ip": ip_address,
                "timestamp": timestamp,
                "ip_location": ip_location,
                "created_at": current_time
            }

        # Send session cookie to browser
        self.send_json(
            {"status": "visitor_recorded"},
            200,
            {
                "Set-Cookie": (
                    f"visitor_id={session_id}; "
                    "Path=/; HttpOnly; SameSite=Lax; "
                    f"Max-Age={SESSION_TIMEOUT}"
                )
            }
        )

    # ==================================================
    # POST REQUESTS
    # ==================================================

    def do_POST(self):

        path = urlsplit(self.path).path

        if path == "/location":

            self.handle_location()
            return

        self.send_error(404, "Route not found")

    # --------------------------------------------------
    # RECEIVE BROWSER GPS DATA
    # --------------------------------------------------

    def handle_location(self):

        try:

            # Read request body
            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            if content_length <= 0 or content_length > MAX_REQUEST_SIZE:
                self.send_json(
                    {"error": "Invalid request size"},
                    400
                )
                return

            body = self.rfile.read(content_length)

            coords = json.loads(
                body.decode("utf-8")
            )

            if not isinstance(coords, dict):
                self.send_json(
                    {"error": "Invalid JSON data"},
                    400
                )
                return

            # Retrieve visitor session
            session_id = self.get_session_id()

            with session_lock:

                visitor = visitor_sessions.pop(
                    session_id, None
                ) if session_id else None

            if visitor is None:

                self.send_json(
                    {
                        "error": "Visitor session not found. "
                                 "Call /track first."
                    },
                    400
                )

                return

            # Visitor information
            ip_address = visitor["ip"]
            timestamp = visitor["timestamp"]

            ip_location = visitor["ip_location"]

            # Browser GPS information
            gps_status = coords.get(
                "status",
                "unavailable"
            )

            if gps_status not in (
                "granted",
                "denied",
                "unavailable"
            ):
                gps_status = "unavailable"

            latitude = None
            longitude = None
            accuracy = None
            gps_link = None

            if gps_status == "granted":

                latitude = coords.get("latitude")
                longitude = coords.get("longitude")
                accuracy = coords.get("accuracy")

                valid_coordinates = (
                    isinstance(latitude, (int, float))
                    and not isinstance(latitude, bool)
                    and math.isfinite(latitude)
                    and -90 <= latitude <= 90
                    and isinstance(longitude, (int, float))
                    and not isinstance(longitude, bool)
                    and math.isfinite(longitude)
                    and -180 <= longitude <= 180
                )

                valid_accuracy = (
                    isinstance(accuracy, (int, float))
                    and not isinstance(accuracy, bool)
                    and math.isfinite(accuracy)
                    and accuracy >= 0
                )

                if not valid_coordinates or not valid_accuracy:

                    self.send_json(
                        {"error": "Invalid GPS data"},
                        400
                    )

                    return

                gps_link = (
                    f"https://www.google.com/maps?q="
                    f"{latitude},{longitude}"
                )

            # IP-based location
            ip_link = (
                ip_location.get("map_link")
                if ip_location else None
            )

            ip_coordinates = (
                f"{ip_location['latitude']}, "
                f"{ip_location['longitude']}"
                if ip_location else "Unavailable"
            )

            location_name = (
                f"{ip_location['city']}, "
                f"{ip_location['region']}, "
                f"{ip_location['country']}"
                if ip_location else "Unavailable"
            )

            ip_accuracy = (
                f"~ {ip_location['accuracy']} meter(s) radius "
                f"({ip_location['accuracy_level'].lower()})"
                if ip_location else "Unavailable"
            )

            # ==================================================
            # UNIFIED TERMINAL OUTPUT
            # ==================================================

            log_entry = f"""------

VISITOR DETECTED [{timestamp}]

[1] IP-BASED LOCATION (ROUGH GEOGRAPHIC ESTIMATE)
> IP ADDRESS       : {ip_address}
> LATITUDE         : {ip_location['latitude'] if ip_location else "Unavailable"}
> LONGITUDE        : {ip_location['longitude'] if ip_location else "Unavailable"}
> ACCURACY         : {ip_accuracy}
> LOCATION         : {location_name}
> GOOGLE MAPS      : {ip_link or "Unavailable"}

[2] BROWSER GPS LOCATION (HIGHER PRECISION ESTIMATE)
> GPS STATUS       : {gps_status.upper()}
> LATITUDE         : {latitude if latitude is not None else "Unavailable"}
> LONGITUDE        : {longitude if longitude is not None else "Unavailable"}
> ACCURACY         : {f"~ {accuracy} meter(s) radius" if accuracy is not None else "Unavailable"}
> GOOGLE MAPS      : {gps_link or "Unavailable"}

> STATUS           : COMPLETED
> SESSION ENDED

------"""

            # Display in terminal
            print(log_entry, flush=True)

            # Send successful response
            self.send_json({
                "status": "ok"
            })

        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:

            print(
                f"[ERROR] Invalid request data: {error}",
                flush=True
            )

            self.send_json(
                {"error": "Invalid request data"},
                400
            )

        except Exception as error:

            print(
                f"[ERROR] Location processing failed: {error}",
                flush=True
            )

            self.send_json(
                {"error": "Internal server error"},
                500
            )


# ==================================================
# CLOUDFLARED TUNNEL AUTOMATION
# ==================================================

def start_cloudflared_tunnel(port):

    cloudflared = shutil.which("cloudflared")

    if cloudflared is None:

        raise RuntimeError(
            "cloudflared was not found on PATH. "
            "Install cloudflared to start the HTTPS tunnel."
        )

    process = subprocess.Popen(
        [
            cloudflared,
            "tunnel",
            "--no-autoupdate",
            "--url",
            f"http://127.0.0.1:{port}"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    def relay_output():

        if process.stdout is None:
            return

        for line in process.stdout:

            print(
                f"[cloudflared] {line}",
                end="",
                flush=True
            )

    threading.Thread(
        target=relay_output,
        daemon=True
    ).start()

    return process


# ==================================================
# MAIN SERVER
# ==================================================

class VisitorServer(ThreadingHTTPServer):

    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":

    print(
        f"Server running locally at http://127.0.0.1:{PORT}"
    )

    server = None
    tunnel = None

    try:

        # Start Cloudflare tunnel
        try:

            tunnel = start_cloudflared_tunnel(PORT)

            print(
                "Starting temporary HTTPS tunnel..."
            )

            print(
                "Waiting for Cloudflare URL..."
            )

        except RuntimeError as error:

            print(
                f"[!] {error}"
            )

        # Start HTTP server
        server = VisitorServer(
            (HOST, PORT),
            VisitorHandler
        )

        print(
            f"HTTP server listening on port {PORT}"
        )

        print(
            "Waiting for visitor requests...\n"
        )

        server.serve_forever()

    except KeyboardInterrupt:

        print("\nShutting down server...")

    finally:

        if server is not None:
            server.server_close()

        if tunnel is not None and tunnel.poll() is None:

            tunnel.terminate()

            try:
                tunnel.wait(timeout=5)

            except subprocess.TimeoutExpired:

                tunnel.kill()
                tunnel.wait()

        print("Server stopped.")
