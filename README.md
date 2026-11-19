# Geo Tracker

A small Python-based web project that demonstrates how a website can collect and display visitor network and location information.

When someone opens the page, the app:
- Detects the visitor's public IP address and looks up an approximate location.
- Requests browser GPS access. If the visitor grants permission, it receives the device's GPS coordinates; otherwise, it records the permission or availability status.
- Collects browser language, time zone, and battery information when supported.
- Prints the collected details in the server terminal.
- Redirects the browser to a configured Instagram Reel after the tracking attempt.

The project uses a temporary **Cloudflare Tunnel** to make the local server accessible through an HTTPS link.

## Preview

<!-- Replace the placeholders below with your screenshots. -->

### Website
![Website screenshot](images/website-preview.png)

### Terminal output
![Terminal output screenshot](images/terminal-output.png)

### Location result
![Location result screenshot](images/location-result.png)

## Tech Stack

- **Python** — HTTP server and request handling
- **HTML & JavaScript** — browser-side location and device information
- **Cloudflare Tunnel (\`cloudflared\`)** — temporary public HTTPS access
- **IP-API** — approximate IP-based geolocation
- **Docker** — optional container-based setup

## Run Locally

### Prerequisites

Install the following:

1. **Python 3.12 or newer** — [Download Python](https://www.python.org/downloads/)
2. **Cloudflared** — [Installation guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
3. **Git** — to clone the repository

No additional Python packages are required. The server uses Python's standard library.

### 1. Clone the repository

\`\`\`bash
git clone https://github.com/prajwal2867/geo-tracker.git
cd geo-tracker
\`\`\`

### 2. Check the installations

\`\`\`bash
python --version
cloudflared --version
\`\`\`

### 3. Start the application

\`\`\`bash
python app.py
\`\`\`

The application starts the local server on:

\`\`\`
http://localhost:5000
\`\`\`

It also starts a Cloudflare Quick Tunnel. Look for the generated \`https://...trycloudflare.com\` URL in the terminal.

Open that HTTPS URL in a browser to access the page from another device. Browser GPS access generally requires HTTPS (or localhost).

Press **Ctrl + C** in the terminal to stop the server and tunnel.

## Optional: Run with Docker

If you have Docker installed, you can run the project without installing Python or Cloudflared separately on your computer. The Docker image includes both.

Build the image:

\`\`\`bash
docker build -t geo-tracker .
\`\`\`

Start the container:

\`\`\`bash
docker run -d --name geo-tracker --restart unless-stopped -p 5000:5000 geo-tracker
\`\`\`

View the server output and generated tunnel URL:

\`\`\`bash
docker logs -f geo-tracker
\`\`\`

Stop the container:

\`\`\`bash
docker stop geo-tracker
\`\`\`

## Important Notes

- **IP-based location is approximate.** It may identify a city or region, not an exact physical address.
- **GPS requires browser permission.** Coordinates are received only when the visitor grants access. If permission is denied or GPS is unavailable, the app reports that status instead.
- **Device information varies by browser.** Battery information, for example, may not be available on every device or browser.
- **Output is terminal-only.** Visitor details are printed in the server terminal (or Docker logs); the app does not save them to a log file.
- **The tunnel is public.** Anyone with the generated URL may be able to access the page. The project does not include authentication.
- **Use responsibly.** Only run this project with people who know what information is being requested and have agreed to participate.

---

Made as a hands-on experiment with Python, browser APIs, and Cloudflare Tunnel.
