FROM cloudflare/cloudflared:latest AS cloudflared

FROM python:3.12-slim

WORKDIR /app

COPY --from=cloudflared /usr/local/bin/cloudflared /usr/local/bin/cloudflared
COPY app.py index.html ./

EXPOSE 5000

CMD ["python", "-u", "app.py"]