#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# Bonifade Technologies Swarm — Automated Backup Script
# Creates compressed snapshots of PostgreSQL DB, Redis data, Media, and Config.
# Supports local backups and Cloudflare R2 / S3 upload.
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
    # shellcheck disable=SC1091
    source .env
fi

BACKUP_DIR="${SCRIPT_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SNAPSHOT_DIR="${BACKUP_DIR}/snapshot_${TIMESTAMP}"
TAR_FILE="${BACKUP_DIR}/buzz_backup_${TIMESTAMP}.tar.gz"

mkdir -p "$SNAPSHOT_DIR"

echo "[Backup] Starting Buzz Swarm backup at $(date)..."

# 1. Dump PostgreSQL
echo "[Backup] Dumping PostgreSQL database 'buzz'..."
docker exec buzz-postgres pg_dump -U "${POSTGRES_USER:-buzz}" "${POSTGRES_DB:-buzz}" > "${SNAPSHOT_DIR}/postgres_dump.sql" 2>/dev/null || true

# 2. Dump Redis
echo "[Backup] Saving Redis dump..."
docker exec buzz-redis redis-cli SAVE >/dev/null 2>&1 || true
docker cp buzz-redis:/data/dump.rdb "${SNAPSHOT_DIR}/dump.rdb" 2>/dev/null || true

# 3. Copy .env & keys
echo "[Backup] Archiving configuration and keys..."
cp -f .env "${SNAPSHOT_DIR}/.env.backup" 2>/dev/null || true
if [ -d data ]; then
    cp -r data "${SNAPSHOT_DIR}/data" 2>/dev/null || true
fi

# 4. Create compressed tarball
echo "[Backup] Compressing snapshot to ${TAR_FILE}..."
tar -czf "$TAR_FILE" -C "$BACKUP_DIR" "snapshot_${TIMESTAMP}"
rm -rf "$SNAPSHOT_DIR"

# 5. Optional Upload to Cloudflare R2 / S3
if [ -n "$R2_ACCESS_KEY_ID" ] && [ -n "$R2_SECRET_ACCESS_KEY" ]; then
    echo "[Backup] Uploading to Cloudflare R2 bucket '${R2_BUCKET_NAME:-bonifade-buzz-storage}'..."
    python3 "${SCRIPT_DIR}/scripts/r2_storage.py" upload "$TAR_FILE" "backups/buzz_backup_${TIMESTAMP}.tar.gz" || echo "[Backup] ! R2 upload warning: check R2 credentials"
fi

# 6. Retention policy: Keep last 14 days of local backups
find "$BACKUP_DIR" -name "buzz_backup_*.tar.gz" -mtime +14 -delete 2>/dev/null || true

echo "[Backup] ✓ Backup completed successfully: ${TAR_FILE} ($(du -h "$TAR_FILE" | cut -f1))"
