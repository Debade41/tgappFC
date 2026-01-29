#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
ENV_FILE="$ROOT_DIR/miniapp/.env"
API_LOG="$ROOT_DIR/miniapp/api_tunnel.log"
WEB_LOG="$ROOT_DIR/miniapp/web_tunnel.log"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE"
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

cd "$ROOT_DIR/miniapp"

docker-compose down --remove-orphans >/dev/null 2>&1 || true
docker-compose up -d --build api

if [ -n "${DIRECT_DOMAIN:-}" ]; then
  API_URL="https://$DIRECT_DOMAIN"
  WEB_URL="https://$DIRECT_DOMAIN"
else
  nohup cloudflared tunnel --url http://localhost:8000 --logfile "$API_LOG" --loglevel info >/dev/null 2>&1 &

  API_URL=""
  for i in $(seq 1 60); do
    API_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$API_LOG" | head -n1 || true)
    if [ -n "$API_URL" ]; then
      break
    fi
    sleep 1
  done

  if [ -z "$API_URL" ]; then
    echo "API tunnel URL not found"
    exit 1
  fi

  nohup cloudflared tunnel --url http://localhost:8080 --logfile "$WEB_LOG" --loglevel info >/dev/null 2>&1 &

  WEB_URL=""
  for i in $(seq 1 60); do
    WEB_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$WEB_LOG" | head -n1 || true)
    if [ -n "$WEB_URL" ]; then
      break
    fi
    sleep 1
  done

  if [ -z "$WEB_URL" ]; then
    echo "Web tunnel URL not found"
    exit 1
  fi
fi

sed -i "s|^VITE_API_URL=.*|VITE_API_URL=$API_URL|" "$ENV_FILE"
sed -i "s|^WEBAPP_URL=.*|WEBAPP_URL=$WEB_URL|" "$ENV_FILE"
sed -i "s|^ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=$WEB_URL|" "$ENV_FILE"

docker-compose up -d --build web

cd "$ROOT_DIR"

if [ -d "$ROOT_DIR/.venv" ]; then
  . "$ROOT_DIR/.venv/bin/activate"
fi

nohup env BOT_TOKEN="$BOT_TOKEN" WEBAPP_URL="$WEB_URL" python3 bot.py > "$ROOT_DIR/bot.log" 2>&1 &

echo "API_URL=$API_URL"
echo "WEB_URL=$WEB_URL"
