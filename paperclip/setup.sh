#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v git >/dev/null
command -v python3 >/dev/null
command -v openssl >/dev/null
docker compose version >/dev/null
if [[ ! -f .env ]]; then
  umask 077
  printf 'PAPERCLIP_REF=50b932a142216331b8d476042b454bc123739c40\nPAPERCLIP_PUBLIC_URL=http://localhost:3100\nPOSTGRES_PASSWORD=%s\nBETTER_AUTH_SECRET=%s\nPAPERCLIP_TOOL_ACTION_SIGNING_SECRET=%s\n' \
    "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" > .env
fi
chmod 600 .env
ref=$(sed -n 's/^PAPERCLIP_REF=//p' .env)
[[ "$ref" =~ ^[0-9a-f]{40}$ ]] || { echo 'PAPERCLIP_REF must be a full commit SHA'; exit 1; }
if [[ ! -d upstream ]]; then
  git clone https://github.com/paperclipai/paperclip.git upstream
fi
[[ -z "$(git -C upstream status --porcelain)" ]] || { echo 'Upstream has local changes; stopping'; exit 1; }
git -C upstream fetch origin "$ref"
git -C upstream checkout --detach "$ref"
python3 knowledge.py index
# The read-only runtime index contains company data, so keep the VPS project private.
chmod 755 ../data
chmod 644 ../data/paperclip-knowledge.sqlite3
docker compose -f compose.yml config --quiet
docker compose -f compose.yml up -d --build
