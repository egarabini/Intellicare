#!/bin/bash
set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/intellicare}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-intellicare-postgres}"
POSTGRES_USER="${POSTGRES_USER:-intellicare_prod}"
POSTGRES_DB="${POSTGRES_DB:-intellicare_prod}"

mkdir -p "$BACKUP_DIR"

docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm -f
echo "[OK] Backup $DATE concluido"
