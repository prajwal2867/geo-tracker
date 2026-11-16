FROM cloudflare/cloudflared:latest AS cloudflared

FROM python:3.12-slim

WORKDIR /app

COPY --from=cloudflared /usr/local/bin/cloudflared /usr/local/bin/cloudflared
COPY geotracker ./geotracker

EXPOSE 8000

CMD ["python", "-u", "-m", "geotracker.server"]
