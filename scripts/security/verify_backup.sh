#!/usr/bin/env bash
# ============================================================================
# IntelliCare — Backup Verification Script
# ============================================================================
# Run: bash scripts/security/verify_backup.sh [backup_archive.tar.gz]
#
# Without an argument, verifies the latest backup.
# ============================================================================
set -euo pipefail

BACKUP_DIR="/var/backups/intellicare"
ARCHIVE="${1:-}"
VERIFY_DIR="/tmp/intellicare-verify"

# Find latest backup if none specified
if [ -z "$ARCHIVE" ]; then
    ARCHIVE=$(ls -t "$BACKUP_DIR"/intellicare_backup_*.tar.gz 2>/dev/null | head -1)
    if [ -z "$ARCHIVE" ]; then
        echo "❌ Nenhum backup encontrado em $BACKUP_DIR"
        exit 1
    fi
fi

echo "============================================================"
echo "  IntelliCare — Verificação de Backup"
echo "  Arquivo: $ARCHIVE"
echo "  Tamanho: $(du -h "$ARCHIVE" | cut -f1)"
echo "  Modificado: $(stat -c '%y' "$ARCHIVE" 2>/dev/null || stat -f '%Sm' "$ARCHIVE")"
echo "============================================================"
echo ""

PASS=0
FAIL=0

check() {
    if [ "$2" = "true" ]; then
        echo "  ✅ $1"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $1"
        FAIL=$((FAIL + 1))
    fi
}

# Extract for analysis
rm -rf "$VERIFY_DIR"
mkdir -p "$VERIFY_DIR"
tar xzf "$ARCHIVE" -C "$VERIFY_DIR"
INNER_DIR=$(ls "$VERIFY_DIR")
VERIFY_PATH="${VERIFY_DIR}/${INNER_DIR}"

echo "📦 Conteúdo do backup:"
echo ""

# 1. PostgreSQL dump
PG_DUMP=$(find "$VERIFY_PATH" -name "postgres_*.sql.gz" -maxdepth 1 | head -1)
if [ -n "$PG_DUMP" ]; then
    PG_SIZE=$(du -h "$PG_DUMP" | cut -f1)
    # Quick integrity check — can we gunzip it?
    if gunzip -t "$PG_DUMP" 2>/dev/null; then
        check "PostgreSQL dump ($PG_SIZE, gzip OK)" "true"

        # Check if it contains platform and tenant schemas
        SCHEMAS_IN_DUMP=$(gunzip -c "$PG_DUMP" | grep -c "CREATE SCHEMA" || echo "0")
        echo "       → $SCHEMAS_IN_DUMP schemas encontrados no dump"
    else
        check "PostgreSQL dump (gzip CORROMPIDO)" "false"
    fi
else
    check "PostgreSQL dump (AUSENTE)" "false"
fi

# 2. Individual schema dumps
SCHEMAS_DIR="${VERIFY_PATH}/schemas"
if [ -d "$SCHEMAS_DIR" ]; then
    SCHEMA_COUNT=$(find "$SCHEMAS_DIR" -name "*.sql.gz" | wc -l)
    echo ""
    echo "  📂 Schema dumps: $SCHEMA_COUNT arquivo(s)"
    for S in "$SCHEMAS_DIR"/*.sql.gz; do
        if [ -f "$S" ]; then
            S_SIZE=$(du -h "$S" | cut -f1)
            if gunzip -t "$S" 2>/dev/null; then
                echo "    ✅ $(basename "$S") ($S_SIZE)"
            else
                echo "    ❌ $(basename "$S") (CORROMPIDO)"
                FAIL=$((FAIL + 1))
            fi
        fi
    done
fi

# 3. Config files
CONFIG_DIR="${VERIFY_PATH}/config"
if [ -d "$CONFIG_DIR" ]; then
    CONFIG_COUNT=$(find "$CONFIG_DIR" -type f | wc -l)
    check "Arquivos de configuração ($CONFIG_COUNT arquivo(s))" "true"

    for CF in "$CONFIG_DIR"/.env*; do
        [ -f "$CF" ] && echo "       → $(basename "$CF")"
    done
else
    check "Arquivos de configuração (AUSENTES)" "false"
fi

# 4. Docker volumes
VOLUMES_DIR="${VERIFY_PATH}/volumes"
if [ -d "$VOLUMES_DIR" ]; then
    VOL_COUNT=$(find "$VOLUMES_DIR" -name "*.tar.gz" | wc -l)
    echo ""
    echo "  📂 Volumes Docker: $VOL_COUNT"
    for V in "$VOLUMES_DIR"/*.tar.gz; do
        if [ -f "$V" ]; then
            V_SIZE=$(du -h "$V" | cut -f1)
            if tar tzf "$V" > /dev/null 2>&1; then
                echo "    ✅ $(basename "$V") ($V_SIZE)"
                PASS=$((PASS + 1))
            else
                echo "    ❌ $(basename "$V") (CORROMPIDO)"
                FAIL=$((FAIL + 1))
            fi
        fi
    done
else
    check "Volumes Docker (AUSENTES)" "false"
fi

# 5. Certificates
CERTS_DIR="${VERIFY_PATH}/certs"
if [ -d "$CERTS_DIR" ]; then
    CERT_FILES=$(find "$CERTS_DIR" -type f | wc -l)
    check "Certificados ($CERT_FILES arquivo(s))" "true"
else
    check "Certificados (ausentes — pode ser OK se não usa Let's Encrypt)" "true"
fi

# Cleanup
rm -rf "$VERIFY_DIR"

# Summary
echo ""
echo "============================================================"
echo "  Resultado: ${PASS} OK, ${FAIL} FALHAS"
if [ "$FAIL" -eq 0 ]; then
    echo "  ✅ Backup íntegro e pronto para restore"
else
    echo "  ⚠️  Backup com problemas — verifique os itens acima"
fi
echo "============================================================"

exit "$FAIL"
