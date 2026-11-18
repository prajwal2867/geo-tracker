# Geolocation Tracker

A Python web server that serves `index.html`, records visitor IP-based location estimates, and requests browser GPS location. Browser GPS is sent only if the visitor grants the browser's location permission. Visitor details are printed to the server output and are not written to a project log file. The redirect destination is fixed to the Instagram Reel URL in `index.html`.

At startup, the server starts a temporary Cloudflare Quick Tunnel. The HTTPS URL appears in the server output and can be opened from another device. The tunnel URL changes when the server restarts.

## Requirements

- Python 3.12 or newer for running directly on your computer. The Docker image uses Python 3.12.
- `cloudflared` installed and available on your `PATH` for direct Python startup.
- A modern browser. Browsers require a secure context (HTTPS, or localhost) for geolocation.
- Docker Desktop or Docker Engine for the optional container setup.

The Python server uses only the standard library; no `pip install` step is needed.

## Run with Python

Open a terminal in the project directory and check the required tools:

```powershell
python --version
cloudflared --version
```

Start the server and tunnel:

```powershell
python app.py
```

The local server listens on `http://localhost:5000`. Open the `https://...trycloudflare.com` URL printed by `cloudflared` to reach it from another device. Press **Ctrl+C** in the server terminal to stop the server and its tunnel.

## Run with Docker

The Docker image includes `cloudflared`, so the server starts its own tunnel inside the container. The destination is fixed in the app; no input or environment variable is needed.

Build the image from the project directory:

```powershell
docker build -t geo-server .
```

If `my-geo-server` already exists, stop and remove it before creating the updated container; rebuilding an image does not change an existing container.

Start the container:

```powershell
docker run -d --name my-geo-server --restart unless-stopped -p 5000:5000 geo-server
```

View the server output and temporary HTTPS URL:

```powershell
docker logs -f my-geo-server
```

Press **Ctrl+C** to stop following logs; this does not stop the container. Restart the container with:

```powershell
docker restart my-geo-server
```

## Location and privacy

The app records visitor IP addresses and rough IP-based location estimates. It also requests browser GPS location, which is sent when the visitor grants browser permission. Location details are printed to the terminal and container output; anyone with access to those outputs can read them. The app does not write a `logs.txt` file. The temporary tunnel makes the server reachable from the public internet. Share its URL only with people who understand and agree to this collection. This project has no authentication.
