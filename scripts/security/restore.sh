#!/usr/bin/env bash
# ============================================================================
# IntelliCare — Backup Restore Script
# ============================================================================
# Usage: sudo bash scripts/security/restore.sh <backup_archive.tar.gz>
#
# ⚠️  WARNING: This will OVERWRITE existing data!
# ============================================================================
set -euo pipefail

ARCHIVE="${1:-}"
RESTORE_DIR="/tmp/intellicare-restore"
COMPOSE_DIR="/opt/INTELLICARE"

DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-intellicare}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }
ok() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1"; }
err() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1"; }

# ── Validation ──────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "❌ Execute como root: sudo bash $0 <arquivo.tar.gz>"
    exit 1
fi

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
    echo "❌ Uso: sudo bash $0 <backup_archive.tar.gz>"
    echo "   Backups disponíveis:"
    ls -la /var/backups/intellicare/intellicare_backup_*.tar.gz 2>/dev/null || echo "   Nenhum backup encontrado"
    exit 1
fi

echo "============================================================"
echo "  IntelliCare — RESTORE from backup"
echo "  Arquivo: $ARCHIVE"
echo "============================================================"
echo ""
echo "  ⚠️  ATENÇÃO: Isso vai SOBRESCREVER os dados atuais!"
echo ""
read -p "  Continuar? [y/N]: " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Restauração cancelada."
    exit 0
fi

# ── Extract ─────────────────────────────────────────────────
log "Extraindo backup..."
rm -rf "$RESTORE_DIR"
mkdir -p "$RESTORE_DIR"

# The archive contains a timestamped directory inside
tar xzf "$ARCHIVE" -C "$RESTORE_DIR"
INNER_DIR=$(ls "$RESTORE_DIR")
RESTORE_PATH="${RESTORE_DIR}/${INNER_DIR}"

ok "Extraído para: $RESTORE_PATH"

# ════════════════════════════════════════════════════════════
# 1. RESTORE PostgreSQL
# ════════════════════════════════════════════════════════════
DUMP_FILE=$(find "$RESTORE_PATH" -name "postgres_*.sql.gz" -maxdepth 1 | head -1)

if [ -n "$DUMP_FILE" ]; then
    log "1/3 — Restaurando PostgreSQL..."

    if docker ps --format '{{.Names}}' | grep -q "postgres"; then
        gunzip -c "$DUMP_FILE" | docker exec -i intellicare-postgres psql -U "$DB_USER"
        ok "PostgreSQL restaurado"
    else
        err "Container postgres não está rodando. Inicie com: docker-compose up -d postgres"
        exit 1
    fi
else
    log "1/3 — Nenhum dump PostgreSQL encontrado, pulando..."
fi

# ════════════════════════════════════════════════════════════
# 2. RESTORE Docker Volumes
# ════════════════════════════════════════════════════════════
log "2/3 — Restaurando volumes Docker..."

VOLUMES_DIR="${RESTORE_PATH}/volumes"
if [ -d "$VOLUMES_DIR" ]; then
    for VOL_ARCHIVE in "$VOLUMES_DIR"/*.tar.gz; do
        if [ -f "$VOL_ARCHIVE" ]; then
            # Extract volume name from filename (e.g. postgres-data_20260222.tar.gz)
            VOL_BASENAME=$(basename "$VOL_ARCHIVE")
            VOL_NAME=$(echo "$VOL_BASENAME" | sed 's/_[0-9]\{8\}.*//')

            if docker volume inspect "$VOL_NAME" &> /dev/null; then
                docker run --rm \
                    -v "${VOL_NAME}:/data" \
                    -v "$(dirname "$VOL_ARCHIVE"):/backup:ro" \
                    alpine sh -c "rm -rf /data/* && tar xzf /backup/$VOL_BASENAME -C /data"
                ok "  Volume: $VOL_NAME"
            else
                log "  Volume não existe, criando: $VOL_NAME"
                docker volume create "$VOL_NAME"
                docker run --rm \
                    -v "${VOL_NAME}:/data" \
                    -v "$(dirname "$VOL_ARCHIVE"):/backup:ro" \
                    alpine tar xzf "/backup/$VOL_BASENAME" -C /data
                ok "  Volume criado e restaurado: $VOL_NAME"
            fi
        fi
    done
else
    log "2/3 — Nenhum backup de volumes encontrado"
fi

# ════════════════════════════════════════════════════════════
# 3. RESTORE Config Files
# ════════════════════════════════════════════════════════════
log "3/3 — Restaurando arquivos de configuração..."

CONFIG_DIR="${RESTORE_PATH}/config"
if [ -d "$CONFIG_DIR" ]; then
    # .env files (only if not present — don't overwrite accidentally)
    for ENV_FILE in "$CONFIG_DIR"/.env*; do
        if [ -f "$ENV_FILE" ]; then
            DEST="${COMPOSE_DIR}/$(basename "$ENV_FILE")"
            if [ -f "$DEST" ]; then
                cp "$DEST" "${DEST}.pre-restore"
                log "  Backup de $(basename "$ENV_FILE") existente → .pre-restore"
            fi
            cp "$ENV_FILE" "$DEST"
            ok "  $(basename "$ENV_FILE")"
        fi
    done
fi

# ── Cleanup ─────────────────────────────────────────────────
rm -rf "$RESTORE_DIR"

echo ""
echo "============================================================"
echo "  ✅ Restore completo!"
echo "============================================================"
echo ""
echo "  Próximos passos:"
echo "  1. Reinicie os containers:"
echo "     docker-compose -f docker-compose.full.yml down"
echo "     docker-compose -f docker-compose.full.yml up -d"
echo "  2. Verifique os healthchecks:"
echo "     docker-compose -f docker-compose.full.yml ps"
echo "  3. Execute o smoke test:"
echo "     bash scripts/smoke_test.sh"
echo "============================================================"
