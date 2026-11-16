import json
import math
import shutil
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


STATIC_DIR = Path(__file__).parent / "static"
MAX_REQUEST_SIZE = 4096


class GeoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'",
        )
        super().end_headers()

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/location":
            self.send_error(404)
            return

        content_length = self.headers.get("Content-Length")
        if content_length is None or not content_length.isdecimal():
            self._send_json(400, {"error": "A valid Content-Length is required."})
            return

        if len(content_length) > len(str(MAX_REQUEST_SIZE)):
            self._send_json(413, {"error": "Request body is too large."})
            return

        size = int(content_length)
        if size > MAX_REQUEST_SIZE:
            self._send_json(413, {"error": "Request body is too large."})
            return

        try:
            coords = json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return

        if not isinstance(coords, dict):
            self._send_json(400, {"error": "Coordinates must be a JSON object."})
            return

        latitude = coords.get("latitude")
        longitude = coords.get("longitude")
        accuracy = coords.get("accuracy")
        if (
            not self._is_finite_number(latitude)
            or not -90 <= latitude <= 90
            or not self._is_finite_number(longitude)
            or not -180 <= longitude <= 180
            or not self._is_finite_number(accuracy)
            or accuracy < 0
        ):
            self._send_json(400, {"error": "Coordinates or accuracy are invalid."})
            return

        print("\n--- Location Received ---")
        print(f"Latitude : {latitude}")
        print(f"Longitude: {longitude}")
        print(f"Accuracy : ~{accuracy} meters")
        print(
            "Google Maps Link: "
            f"https://www.google.com/maps?q={latitude},{longitude}"
        )
        print("-------------------------\n")
        self._send_json(200, {"status": "ok"})

    @staticmethod
    def _is_finite_number(value):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        try:
            return math.isfinite(value)
        except OverflowError:
            return False


def start_cloudflared_tunnel(port):
    cloudflared = shutil.which("cloudflared")
    if cloudflared is None:
        raise RuntimeError(
            "cloudflared was not found on PATH. Install cloudflared to start "
            "the HTTPS tunnel."
        )

    process = subprocess.Popen(
        [
            cloudflared,
            "tunnel",
            "--no-autoupdate",
            "--url",
            f"http://127.0.0.1:{port}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def relay_output():
        if process.stdout is None:
            return
        for line in process.stdout:
            print(f"[cloudflared] {line}", end="")

    threading.Thread(target=relay_output, daemon=True).start()
    return process


def main():
    port = 8000
    server = ThreadingHTTPServer(("0.0.0.0", port), GeoHandler)
    print(f"Server running locally at http://0.0.0.0:{port}")
    tunnel = None
    try:
        tunnel = start_cloudflared_tunnel(port)
        print("Starting a temporary HTTPS tunnel; its URL will appear below.")
        print("Waiting for connections...")
        server.serve_forever()
    except RuntimeError as error:
        raise SystemExit(str(error)) from error
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()
        if tunnel is not None and tunnel.poll() is None:
            tunnel.terminate()
            try:
                tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.kill()
                tunnel.wait()


if __name__ == "__main__":
    main()
