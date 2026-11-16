# Geolocation Tracker

A small Python web server that serves a page for sharing a device's location. When the visitor clicks **Share my location** and grants the browser's location permission, the page sends the coordinates to the server. The server prints the coordinates, reported accuracy, and a Google Maps link in its console. It does not save locations to a database.

When the server starts, it also launches a temporary Cloudflare Quick Tunnel. The HTTPS URL appears in the server output and can be opened from another device. The URL is temporary and changes when the tunnel is restarted.

## Requirements

- Python 3.12 or newer for running directly on your computer. The Docker image uses Python 3.12.
- `cloudflared` installed and available on your `PATH` for direct Python startup.
- A modern browser with location services enabled. Browsers require a secure context (HTTPS, or localhost) for geolocation.
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
python server.py
```

Open the `https://...trycloudflare.com` URL printed by `cloudflared`. The local page is also available at `http://localhost:8000`. Click **Share my location** and approve the browser's location prompt to send it. Press **Ctrl+C** in the server terminal to stop both the server and its tunnel.

## Run with Docker

The Docker image includes `cloudflared`, so the server starts its own tunnel inside the container.

Build the image:

```powershell
docker build -t geo-server .
```

Start the container in the background:

```powershell
docker run -d --name my-geo-server --restart unless-stopped -p 8000:8000 geo-server
```

Show the server and tunnel output (including the HTTPS URL):

```powershell
docker logs -f my-geo-server
```

Press **Ctrl+C** to stop following the logs; this does not stop the container. Use these commands to stop or restart it:

```powershell
docker stop my-geo-server
docker start my-geo-server
```

Each container start creates a new temporary tunnel URL. To remove the container after stopping it:

```powershell
docker rm my-geo-server
```

## Location and privacy

Location is sent only after the visitor clicks the button and grants browser permission. The server prints the coordinates to its logs; anyone who can read those logs can see them. The temporary tunnel makes the server reachable from the public internet, so share its URL only with people you trust. This project has no authentication or persistent storage.
