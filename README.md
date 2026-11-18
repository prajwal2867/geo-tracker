# Geolocation Tracker

A Python web server that serves `index.html`, records visitor IP-based location estimates, and requests browser GPS location. Browser GPS is sent only if the visitor grants the browser's location permission. The server prints visitor details to its console and appends them to `logs.txt`; it does not use a database.

At startup, the server asks for the destination URL to redirect visitors to after tracking. It also starts a temporary Cloudflare Quick Tunnel. The HTTPS URL appears in the server output and can be opened from another device. The tunnel URL changes when the server restarts.

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

Start the server and tunnel. Enter the destination URL when prompted:

```powershell
python app.py
```

The local server listens on `http://localhost:5000`. Open the `https://...trycloudflare.com` URL printed by `cloudflared` to reach it from another device. Press **Ctrl+C** in the server terminal to stop the server and its tunnel.

## Run with Docker

The Docker image includes `cloudflared`, so the server starts its own tunnel inside the container. Run it attached to a terminal so you can enter the destination URL at each start.

Build the image from the project directory:

```powershell
docker build -t geo-server .
```

Start the container interactively and mount the project `logs.txt` into it. This keeps the log on the host even if you remove the container:

```powershell
docker run -it --name my-geo-server -p 5000:5000 --mount "type=bind,source=$((Get-Location).Path)\logs.txt,target=/app/logs.txt" geo-server
```

Enter the destination URL when prompted. The server and tunnel output, including the temporary HTTPS URL, appears in this terminal. Press **Ctrl+C** to stop the container.

To start the same container again and answer the prompt, use:

```powershell
docker start -ai my-geo-server
```

`logs.txt` is written in the project directory through the bind mount and remains after stopping or removing the container. The tunnel URL is temporary and changes each time the app starts. To remove the container:

```powershell
docker rm my-geo-server
```

## Location and privacy

The app records visitor IP addresses and rough IP-based location estimates. It also requests browser GPS location, which is sent when the visitor grants browser permission. Location details are printed to the terminal and saved in `logs.txt`; anyone with access to the terminal, container logs, or mounted log file can read them. The temporary tunnel makes the server reachable from the public internet. Share its URL only with people who understand and agree to this collection. This project has no authentication.
