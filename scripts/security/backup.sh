#!/usr/bin/env bash
# ============================================================================
# IntelliCare — Automated Backup Script
# ============================================================================
# Run: sudo bash scripts/security/backup.sh
# Schedule via cron: 0 2 * * * /opt/INTELLICARE/scripts/security/backup.sh
# ============================================================================
set -euo pipefail

# ── Configuration ───────────────────────────────────────────
BACKUP_DIR="/var/backups/intellicare"
RETENTION_DAYS=30
COMPOSE_DIR="/opt/INTELLICARE"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
LOG_FILE="/var/log/intellicare-backup.log"

# Database settings (from .env or defaults)
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-intellicare}"
DB_PASSWORD="${POSTGRES_PASSWORD:-}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
ok() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1" | tee -a "$LOG_FILE"; }
err() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1" | tee -a "$LOG_FILE"; }

# ── Check root ──────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "❌ Execute como root: sudo bash $0"
    exit 1
fi

echo "============================================================"
echo "  IntelliCare — Backup ${TIMESTAMP}"
echo "============================================================"

mkdir -p "$BACKUP_PATH"

# ════════════════════════════════════════════════════════════
# 1. PostgreSQL Full Dump (all schemas incl. platform + tenants)
# ════════════════════════════════════════════════════════════
log "1/5 — Backup PostgreSQL..."

DUMP_FILE="${BACKUP_PATH}/postgres_${DB_NAME}_${TIMESTAMP}.sql.gz"

# Prefer Docker exec if postgres container exists
if docker ps --format '{{.Names}}' | grep -q "postgres"; then
    docker exec intellicare-postgres pg_dumpall -U "$DB_USER" \
        | gzip > "$DUMP_FILE"
    ok "PostgreSQL dump (via Docker): $(du -h "$DUMP_FILE" | cut -f1)"
elif command -v pg_dumpall &> /dev/null; then
    PGPASSWORD="$DB_PASSWORD" pg_dumpall -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
        | gzip > "$DUMP_FILE"
    ok "PostgreSQL dump (via pg_dumpall): $(du -h "$DUMP_FILE" | cut -f1)"
else
    err "pg_dumpall não encontrado e container postgres não está rodando"
fi

# ════════════════════════════════════════════════════════════
# 2. Individual Tenant Schema Dumps
# ════════════════════════════════════════════════════════════
log "2/5 — Backup de schemas individuais..."

SCHEMAS_DIR="${BACKUP_PATH}/schemas"
mkdir -p "$SCHEMAS_DIR"

if docker ps --format '{{.Names}}' | grep -q "postgres"; then
    # Get list of tenant schemas
    SCHEMAS=$(docker exec intellicare-postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%' OR schema_name = 'platform';" 2>/dev/null || echo "")

    if [ -n "$SCHEMAS" ]; then
        for SCHEMA in $SCHEMAS; do
            SCHEMA_FILE="${SCHEMAS_DIR}/${SCHEMA}_${TIMESTAMP}.sql.gz"
            docker exec intellicare-postgres pg_dump -U "$DB_USER" -d "$DB_NAME" \
                --schema="$SCHEMA" | gzip > "$SCHEMA_FILE"
            ok "  Schema: $SCHEMA ($(du -h "$SCHEMA_FILE" | cut -f1))"
        done
    else
        log "  Nenhum schema tenant encontrado"
    fi
fi

# ════════════════════════════════════════════════════════════
# 3. Environment Files
# ════════════════════════════════════════════════════════════
log "3/5 — Backup de arquivos de configuração..."

CONFIG_DIR="${BACKUP_PATH}/config"
mkdir -p "$CONFIG_DIR"

# .env files
for ENV_FILE in "$COMPOSE_DIR"/.env "$COMPOSE_DIR"/.env.production "$COMPOSE_DIR"/.env.local; do
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$CONFIG_DIR/"
        ok "  $(basename "$ENV_FILE")"
    fi
done

# Docker compose files
cp "$COMPOSE_DIR"/docker-compose*.yml "$CONFIG_DIR/" 2>/dev/null || true

# Traefik config
if [ -d "$COMPOSE_DIR/traefik" ]; then
    cp -r "$COMPOSE_DIR/traefik" "$CONFIG_DIR/traefik"
    ok "  traefik/ config"
fi

# ════════════════════════════════════════════════════════════
# 4. Docker Volumes
# ════════════════════════════════════════════════════════════
log "4/5 — Backup de volumes Docker..."

VOLUMES_DIR="${BACKUP_PATH}/volumes"
mkdir -p "$VOLUMES_DIR"

# Key volumes to backup
VOLUMES=(
    "intellicare_postgres-data"
    "intellicare_redis-data"
    "intellicare_prometheus-data"
    "intellicare_grafana-data"
    "intellicare_letsencrypt-data"
)

for VOL in "${VOLUMES[@]}"; do
    if docker volume inspect "$VOL" &> /dev/null; then
        VOL_FILE="${VOLUMES_DIR}/${VOL}_${TIMESTAMP}.tar.gz"
        docker run --rm \
            -v "${VOL}:/data:ro" \
            -v "${VOLUMES_DIR}:/backup" \
            alpine tar czf "/backup/$(basename "$VOL_FILE")" -C /data .
        ok "  Volume: $VOL ($(du -h "$VOL_FILE" | cut -f1))"
    else
        log "  Volume não existe: $VOL"
    fi
done

# ════════════════════════════════════════════════════════════
# 5. Let's Encrypt Certificates
# ════════════════════════════════════════════════════════════
log "5/5 — Backup de certificados..."

CERTS_DIR="${BACKUP_PATH}/certs"
mkdir -p "$CERTS_DIR"

# Traefik ACME storage
if docker volume inspect "intellicare_letsencrypt-data" &> /dev/null; then
    docker run --rm \
        -v "intellicare_letsencrypt-data:/data:ro" \
        -v "${CERTS_DIR}:/backup" \
        alpine cp -r /data/. /backup/
    ok "  Certificados Let's Encrypt"
fi

# ════════════════════════════════════════════════════════════
# COMPRESS & CLEANUP
# ════════════════════════════════════════════════════════════
log "Comprimindo backup final..."

ARCHIVE="${BACKUP_DIR}/intellicare_backup_${TIMESTAMP}.tar.gz"
tar czf "$ARCHIVE" -C "$BACKUP_DIR" "$TIMESTAMP"
rm -rf "$BACKUP_PATH"
ok "Arquivo final: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

# Retention policy
log "Limpando backups antigos (>${RETENTION_DAYS} dias)..."
DELETED=$(find "$BACKUP_DIR" -name "intellicare_backup_*.tar.gz" -mtime +"$RETENTION_DAYS" -delete -print | wc -l)
ok "Removidos: $DELETED backups antigos"

# ════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "  ✅ Backup completo!"
echo "============================================================"
echo ""
echo "  Arquivo: $ARCHIVE"
echo "  Tamanho: $(du -h "$ARCHIVE" | cut -f1)"
echo "  Retenção: ${RETENTION_DAYS} dias"
echo "  Log: $LOG_FILE"
echo ""
echo "  📌 Para restaurar:"
echo "  sudo bash scripts/security/restore.sh $ARCHIVE"
echo "============================================================"
