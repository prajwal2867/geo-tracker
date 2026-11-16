from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import shutil
import subprocess
import threading


class GeoHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/location':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                coords = json.loads(post_data.decode('utf-8'))
                lat = coords.get('latitude')
                lon = coords.get('longitude')
                acc = coords.get('accuracy')

                print("\n--- Location Received ---")
                print(f"Latitude : {lat}")
                print(f"Longitude: {lon}")
                print(f"Accuracy : ~{acc} meters")
                print(f"Google Maps Link: https://www.google.com/maps?q={lat},{lon}")
                print("-------------------------\n")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
            except Exception as error:
                print(f"Error parsing data: {error}")
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def start_cloudflared_tunnel(port):
    cloudflared = shutil.which('cloudflared')
    if cloudflared is None:
        raise RuntimeError(
            "cloudflared was not found on PATH. Install cloudflared to start "
            "the HTTPS tunnel."
        )

    process = subprocess.Popen(
        [
            cloudflared,
            'tunnel',
            '--no-autoupdate',
            '--url',
            f'http://127.0.0.1:{port}',
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
            print(f"[cloudflared] {line}", end='')

    threading.Thread(target=relay_output, daemon=True).start()
    return process


if __name__ == '__main__':
    port = 8000
    server = HTTPServer(('0.0.0.0', port), GeoHandler)
    print(f"Server running locally at http://0.0.0.0:{port}")
    tunnel = None
    try:
        tunnel = start_cloudflared_tunnel(port)
        print("Starting a temporary HTTPS tunnel; its URL will appear below.")
        print("Waiting for connections...")
        server.serve_forever()
    except RuntimeError as error:
        server.server_close()
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
