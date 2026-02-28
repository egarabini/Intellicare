#!/bin/bash
# Script para refresh de materialized views do módulo de comunicação
# Deve ser executado via cron a cada hora
#
# Exemplo de crontab:
# 0 * * * * /path/to/refresh_materialized_views.sh >> /var/log/intellicare/comunicacao_mv_refresh.log 2>&1

set -e

# Configuração
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-intellicare}"
DB_USER="${DB_USER:-intellicare_user}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Timestamp
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando refresh de materialized views..."

# Executar refresh via psql
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT comunicacao_analitico.refresh_materialized_views();"

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Refresh concluído com sucesso!"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERRO: Falha no refresh das materialized views!"
    exit 1
fi

