#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v git >/dev/null
command -v python3 >/dev/null
command -v openssl >/dev/null
docker compose version >/dev/null
if [[ ! -f .env ]]; then
  umask 077
  printf 'PAPERCLIP_PUBLIC_URL=https://company.bonifadetechnologies.com\nPOSTGRES_PASSWORD=%s\nBETTER_AUTH_SECRET=%s\nPAPERCLIP_TOOL_ACTION_SIGNING_SECRET=%s\n' \
    "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" > .env
fi
# Upgrade the original localhost default without rotating existing secrets.
sed -i 's|^PAPERCLIP_PUBLIC_URL=http://localhost:3100$|PAPERCLIP_PUBLIC_URL=https://company.bonifadetechnologies.com|' .env
chmod 600 .env
python3 knowledge.py index
# The read-only runtime index contains company data, so keep the VPS project private.
chmod 755 ../data
chmod 644 ../data/paperclip-knowledge.sqlite3
docker compose -f compose.yml config --quiet
docker compose -f compose.yml pull
docker compose -f compose.yml up -d --no-build
