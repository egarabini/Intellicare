#!/bin/bash
# =============================================================================
# IntelliCare V3 — Clean-Slate Deploy (Staging)
# Uso: bash staging_clean_deploy.sh [branch]
# Exemplo: bash staging_clean_deploy.sh main
# AVISO: apaga TUDO no servidor — volumes, imagens, containers, código antigo.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
BRANCH="${1:-main}"
REPO_URL="https://github.com/egarabini/Intellicare.git"
DEPLOY_DIR="/opt/intellicare"
COMPOSE_FILE="infra/docker-compose.yml"
# Auto-detecta env: .env.staging tem prioridade sobre .env
if [ -f "$DEPLOY_DIR/infra/.env.staging" ]; then
  ENV_FILE="infra/.env.staging"
elif [ -f "$DEPLOY_DIR/infra/.env" ]; then
  ENV_FILE="infra/.env"
else
  fail "Nenhum .env encontrado em $DEPLOY_DIR/infra/ — crie o arquivo antes de rodar este script"
fi
LOG_FILE="/var/log/intellicare_deploy.log"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN: $1${NC}" | tee -a "$LOG_FILE"; }
fail() { echo -e "${RED}[$(date '+%H:%M:%S')] ERRO: $1${NC}" | tee -a "$LOG_FILE"; exit 1; }

log "========================================================"
log "  IntelliCare V3 — Clean-Slate Deploy  (branch: $BRANCH)"
log "========================================================"

# ---------------------------------------------------------------------------
# 1. Parar e remover TUDO que está rodando
# ---------------------------------------------------------------------------
log "PASSO 1 — Parando todos os containers IntelliCare..."

if [ -d "$DEPLOY_DIR" ]; then
  cd "$DEPLOY_DIR"
  if [ -f "$COMPOSE_FILE" ]; then
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down \
      --volumes --remove-orphans --timeout 30 2>/dev/null || warn "compose down falhou (ignorando)"
  fi
fi

log "PASSO 1 — Removendo containers parados restantes..."
docker ps -aq --filter "name=intellicare" | xargs -r docker rm -f 2>/dev/null || true

# ---------------------------------------------------------------------------
# 2. Limpar imagens, volumes e networks do IntelliCare
# ---------------------------------------------------------------------------
log "PASSO 2 — Removendo imagens IntelliCare (force)..."
docker images --format "{{.Repository}}:{{.Tag}}" | grep -i intellicare | \
  xargs -r docker rmi -f 2>/dev/null || true

log "PASSO 2 — Removendo volumes IntelliCare..."
docker volume ls --format "{{.Name}}" | grep -i intellicare | \
  xargs -r docker volume rm -f 2>/dev/null || true

log "PASSO 2 — Removendo networks IntelliCare..."
docker network ls --format "{{.Name}}" | grep -i intellicare | \
  xargs -r docker network rm 2>/dev/null || true

log "PASSO 2 — Limpando build cache Docker (liberar espaço)..."
docker builder prune -af 2>/dev/null || true

log "PASSO 2 — Espaço em disco após limpeza:"
df -h / | tail -1

# ---------------------------------------------------------------------------
# 3. Remover código antigo e clonar fresh
# ---------------------------------------------------------------------------
log "PASSO 3 — Removendo repositório antigo: $DEPLOY_DIR"
rm -rf "$DEPLOY_DIR"

log "PASSO 3 — Clonando branch '$BRANCH' de $REPO_URL..."
git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$DEPLOY_DIR" || \
  fail "git clone falhou — verificar URL e branch"

cd "$DEPLOY_DIR"
log "PASSO 3 — Commit HEAD: $(git log --oneline -1)"

# ---------------------------------------------------------------------------
# 4. Verificar .env
# ---------------------------------------------------------------------------
log "PASSO 4 — Verificando arquivo de ambiente: $ENV_FILE"
if [ ! -f "$ENV_FILE" ]; then
  fail "$ENV_FILE não encontrado. Crie o arquivo antes de rodar este script."
fi

# Validar variáveis críticas
REQUIRED_VARS=(
  POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB POSTGRES_HOST
  REDIS_HOST KEYCLOAK_ADMIN KEYCLOAK_ADMIN_PASSWORD
)
for VAR in "${REQUIRED_VARS[@]}"; do
  if ! grep -q "^${VAR}=" "$ENV_FILE"; then
    fail "Variável $VAR não encontrada em $ENV_FILE"
  fi
done
log "PASSO 4 — .env validado (${#REQUIRED_VARS[@]} variáveis críticas OK)"

# ---------------------------------------------------------------------------
# 5. Build completo sem cache
# ---------------------------------------------------------------------------
log "PASSO 5 — Build das imagens (--no-cache)... isso pode levar 5-10 min"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" \
  build --no-cache --parallel 2>&1 | tee -a "$LOG_FILE" || \
  fail "Build falhou — ver log acima"

# ---------------------------------------------------------------------------
# 6. Subir infra primeiro (postgres, redis, keycloak)
# ---------------------------------------------------------------------------
log "PASSO 6 — Subindo serviços de infra (postgres, redis, keycloak, traefik)..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" \
  up -d postgres redis traefik 2>&1 | tee -a "$LOG_FILE"

log "PASSO 6 — Aguardando PostgreSQL ficar healthy (máx 60s)..."
for i in $(seq 1 12); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' intellicare-postgres 2>/dev/null || echo "missing")
  if [ "$STATUS" = "healthy" ]; then
    log "PASSO 6 — PostgreSQL healthy ✓"
    break
  fi
  warn "PostgreSQL status: $STATUS (tentativa $i/12)..."
  sleep 5
  [ $i -eq 12 ] && fail "PostgreSQL não ficou healthy em 60s"
done

log "PASSO 6 — Subindo Keycloak..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" \
  up -d keycloak 2>&1 | tee -a "$LOG_FILE"

log "PASSO 6 — Aguardando Keycloak ficar healthy (máx 120s)..."
for i in $(seq 1 24); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' intellicare-keycloak 2>/dev/null || echo "missing")
  if [ "$STATUS" = "healthy" ]; then
    log "PASSO 6 — Keycloak healthy ✓"
    break
  fi
  warn "Keycloak status: $STATUS (tentativa $i/24)..."
  sleep 5
  [ $i -eq 24 ] && fail "Keycloak não ficou healthy em 120s"
done

# ---------------------------------------------------------------------------
# 7. Configurar Keycloak (realm + clients + users)
# ---------------------------------------------------------------------------
log "PASSO 7 — Configurando Keycloak (realm, clients, usuários de seed)..."
python3 tools/scripts/setup_keycloak.py \
  --keycloak-url http://localhost:8080 \
  --seed-demo-users 2>&1 | tee -a "$LOG_FILE" || \
  warn "setup_keycloak.py retornou erro — verificar log (Keycloak pode já estar configurado)"

# ---------------------------------------------------------------------------
# 8. Subir demais serviços
# ---------------------------------------------------------------------------
log "PASSO 8 — Subindo todos os serviços restantes..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" \
  up -d 2>&1 | tee -a "$LOG_FILE" || \
  fail "docker compose up -d falhou"

log "PASSO 8 — Aguardando intellicare-service ficar healthy (máx 90s)..."
for i in $(seq 1 18); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' intellicare-service 2>/dev/null || echo "missing")
  if [ "$STATUS" = "healthy" ]; then
    log "PASSO 8 — intellicare-service healthy ✓"
    break
  fi
  warn "intellicare-service status: $STATUS (tentativa $i/18)..."
  sleep 5
  [ $i -eq 18 ] && fail "intellicare-service não ficou healthy em 90s"
done

# ---------------------------------------------------------------------------
# 9. Validação final
# ---------------------------------------------------------------------------
log "PASSO 9 — Validação dos endpoints..."

check_http() {
  local URL=$1; local LABEL=$2
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL" 2>/dev/null || echo "000")
  if [[ "$HTTP" == "200" || "$HTTP" == "302" || "$HTTP" == "301" ]]; then
    log "  ✓ $LABEL → HTTP $HTTP"
  else
    warn "  ✗ $LABEL → HTTP $HTTP (pode ser normal se ainda inicializando)"
  fi
}

HOST_PORT=$(grep -oP '(?<=^\")[0-9]+(?=:8000)' "$ENV_FILE" 2>/dev/null | head -1 || echo "9000")

check_http "http://localhost:${HOST_PORT}/health"         "API /health"
check_http "http://localhost:${HOST_PORT}/admin-ui/"      "AdminUI"
check_http "http://localhost:${HOST_PORT}/gestor-ui/"     "GestorUI"
check_http "http://localhost:${HOST_PORT}/clinico-ui/"    "ClinicoUI"
check_http "http://localhost:${HOST_PORT}/paciente-ui/"   "PacienteUI"
check_http "http://localhost:8080/realms/intellicare"     "Keycloak realm"

# ---------------------------------------------------------------------------
# 10. Status final
# ---------------------------------------------------------------------------
log "PASSO 10 — Status dos containers:"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps \
  --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || \
  docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep intellicare

log "========================================================"
log "  DEPLOY CONCLUÍDO — branch: $BRANCH"
log "  Log completo: $LOG_FILE"
log "========================================================"
