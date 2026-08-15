#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# Bonifade Technologies Swarm — Restore Script
# Restores PostgreSQL DB, Redis data, and configs from a backup tarball.
#
# Usage:
#   ./scripts/restore.sh [path/to/buzz_backup_TIMESTAMP.tar.gz]
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
    # shellcheck disable=SC1091
    source .env
fi

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <path_to_backup_tarball.tar.gz>"
    echo "Available backups in backups/:"
    ls -lht backups/buzz_backup_*.tar.gz 2>/dev/null || echo "No backups found."
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' does not exist."
    exit 1
fi

echo "⚠️  WARNING: This will restore database and state from: $BACKUP_FILE"
read -p "Are you sure you want to proceed? [y/N]: " -r CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
    echo "Restore cancelled."
    exit 0
fi

TMP_DIR="/tmp/buzz_restore_$(date +%s)"
mkdir -p "$TMP_DIR"

echo "[Restore] Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$TMP_DIR"
EXTRACTED_DIR=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)

# 1. Restore PostgreSQL
if [ -f "${EXTRACTED_DIR}/postgres_dump.sql" ]; then
    echo "[Restore] Restoring PostgreSQL database..."
    docker exec -i buzz-postgres psql -U "${POSTGRES_USER:-buzz}" -d "${POSTGRES_DB:-buzz}" < "${EXTRACTED_DIR}/postgres_dump.sql"
    echo "[Restore] ✓ PostgreSQL database restored."
fi

# 2. Restore Redis
if [ -f "${EXTRACTED_DIR}/dump.rdb" ]; then
    echo "[Restore] Restoring Redis snapshot..."
    docker stop buzz-redis
    docker cp "${EXTRACTED_DIR}/dump.rdb" buzz-redis:/data/dump.rdb
    docker start buzz-redis
    echo "[Restore] ✓ Redis data restored."
fi

# 3. Restore data directory
if [ -d "${EXTRACTED_DIR}/data" ]; then
    echo "[Restore] Restoring keypair and state data..."
    cp -rn "${EXTRACTED_DIR}/data/"* data/ 2>/dev/null || true
fi

rm -rf "$TMP_DIR"
echo "[Restore] 🎉 Restore completed successfully!"
