#!/usr/bin/env bash
set -euo pipefail

cat > .env <<EOF
DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN:-}
DISCORD_DEV_GUILD_ID=${DISCORD_DEV_GUILD_ID:-}
ALLOW_DM_SUBSCRIPTIONS=${ALLOW_DM_SUBSCRIPTIONS:-false}
DISCORD_SHOW_THUMBNAILS=${DISCORD_SHOW_THUMBNAILS:-true}
WEB_API_BASE_URL=${WEB_API_BASE_URL:-https://feed.raupulus.dev}
WEB_API_TIMEOUT_SECONDS=${WEB_API_TIMEOUT_SECONDS:-10}
REVERB_WS_URL=${REVERB_WS_URL:-wss://feed.raupulus.dev}
REVERB_APP_KEY=${REVERB_APP_KEY:-beacon-sift-public-key}
REVERB_CHANNEL=${REVERB_CHANNEL:-beacon.news}
BOT_DB_PATH=${BOT_DB_PATH:-/app/data/bot.db}
BOT_TIMEZONE=${BOT_TIMEZONE:-Europe/Madrid}
LOG_LEVEL=${LOG_LEVEL:-INFO}
EOF

chmod 0640 .env

if [[ -n "${PATH_INSTALL:-}" ]] && [[ -d "${PATH_INSTALL}" ]]; then
    cp -f .env "${PATH_INSTALL}/.env"
    chmod 0640 "${PATH_INSTALL}/.env"
fi

echo "✅ Archivo .env generado correctamente para beacon-sift-bot-discord."
