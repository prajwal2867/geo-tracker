# Geo Tracker

A small Python web server that serves a page which requests browser geolocation
and, after the visitor grants permission, prints the coordinates and a map link
to the server's console. It does not write coordinates to an application
database or file.

## Requirements

- Python 3.12 or newer
- `cloudflared` on `PATH` (the server starts a temporary Cloudflare Quick Tunnel
  automatically)

## Run locally

```powershell
python -m geotracker.server
```

Open the HTTPS URL printed by `cloudflared` and allow the browser's location
permission when prompted. The page also provides a button to request location
again. The server listens on port 8000.

## Run with Docker

```powershell
docker build -t geo-server .
docker run -d --name my-geo-server --restart unless-stopped -p 8000:8000 geo-server
docker logs -f my-geo-server
```

The temporary HTTPS URL appears in the container logs. Stop and remove the
container with:

```powershell
docker stop my-geo-server
docker rm my-geo-server
```

## Privacy and deployment

- The page requests geolocation when it loads. The browser must grant permission
  before coordinates are sent; permission can be denied or revoked in browser
  settings.
- The server prints received coordinates to standard output. Container logs may
  retain that output; handle and clear logs according to your privacy needs.
- The Quick Tunnel makes the server reachable through a public URL. Anyone with
  that URL can submit requests, and this minimal app has no authentication,
  rate-limiting, or persistence controls. Do not use it for sensitive or
  production workloads, and do not share the tunnel URL unnecessarily.

## Project layout

```text
geotracker/
  __init__.py
  server.py
  static/
    app.js
    index.html
tests/
  test_server.py
```

## Tests

```powershell
python -m unittest discover -s tests -v
```
