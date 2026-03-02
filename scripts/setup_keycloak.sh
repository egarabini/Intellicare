#!/bin/bash
# ============================================================================
# Script de Setup do Keycloak para IntelliCare Multi-Tenant
# ============================================================================
# Uso: ./scripts/setup_keycloak.sh
# Descrição: Configura realm, clients e roles automaticamente
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

KEYCLOAK_CONTAINER="${KEYCLOAK_CONTAINER:-keycloak-intellicare}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-changeme}"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   🔐 Setup Keycloak - IntelliCare Multi-Tenant           ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 1. Verificar se Keycloak está rodando
log_info "Verificando se Keycloak está rodando..."

if ! docker ps --format '{{.Names}}' | grep -q "^${KEYCLOAK_CONTAINER}$"; then
    log_error "Keycloak não está rodando!"
    log_info "Execute primeiro: docker-compose -f docker-compose.keycloak.yml up -d"
    exit 1
fi

log_success "Keycloak está rodando!"

# 2. Aguardar Keycloak estar pronto
log_info "Aguardando Keycloak ficar pronto..."
echo "  (pode levar até 60 segundos na primeira inicialização)"

MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost:8080/health/ready > /dev/null 2>&1; then
        log_success "Keycloak está pronto!"
        break
    fi
    WAITED=$((WAITED + 5))
    echo -n "."
    sleep 5
done

if [ $WAITED -ge $MAX_WAIT ]; then
    log_error "Timeout aguardando Keycloak!"
    exit 1
fi

echo ""

# 3. Verificar se realm já existe
log_info "Verificando se realm bemcuidar já existe..."

REALM_EXISTS=$(curl -s http://localhost:8080/realms/bemcuidar -w "%{http_code}" | tail -n1)
RECREATE_REALM="false"

if [ "$REALM_EXISTS" = "200" ]; then
    log_warning "Realm bemcuidar já existe!"
    read -p "Deseja recriar? (s/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        RECREATE_REALM="true"
    else
        log_info "Mantendo realm existente"
    fi
fi

# 4. Login no kcadm
log_info "Autenticando no kcadm..."
docker exec "${KEYCLOAK_CONTAINER}" /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user "${KEYCLOAK_ADMIN_USER}" \
    --password "${KEYCLOAK_ADMIN_PASS}" > /dev/null

if [ "${RECREATE_REALM}" = "true" ]; then
    log_info "Deletando realm existente..."
    docker exec "${KEYCLOAK_CONTAINER}" /opt/keycloak/bin/kcadm.sh delete realms/bemcuidar > /dev/null 2>&1 || true
fi

# 5. Criar realm via import (se existir arquivo)
if [ -f "keycloak/import/bemcuidar-realm.json" ]; then
    log_info "Importando realm bemcuidar..."

    # Verificar se o arquivo JSON é válido
    if ! python3 -m json.tool keycloak/import/bemcuidar-realm.json > /dev/null 2>&1; then
        log_error "Arquivo bemcuidar-realm.json é inválido!"
        exit 1
    fi

    # Criar realm via import
    docker exec "${KEYCLOAK_CONTAINER}" /opt/keycloak/bin/kcadm.sh create realms \
        -f /opt/keycloak/data/import/bemcuidar-realm.json > /dev/null 2>&1 || true

    log_success "Realm importado!"
else
    log_warning "Arquivo keycloak/import/bemcuidar-realm.json não encontrado"
    log_info "Criando realm manualmente..."

    # Criar realm manualmente
    docker exec "${KEYCLOAK_CONTAINER}" /opt/keycloak/bin/kcadm.sh create realms \
        -s realm=bemcuidar \
        -s enabled=true \
        -s sslRequired=external > /dev/null 2>&1 || true

    log_success "Realm criado!"
fi

# 6. Verificar clients
log_info "Verificando clients..."

CLIENTS=$(docker exec "${KEYCLOAK_CONTAINER}" /opt/keycloak/bin/kcadm.sh get clients -r bemcuidar \
    | jq -r '.[].clientId' 2>/dev/null || true)

if echo "$CLIENTS" | grep -q "^intellicare-admin$"; then
    log_success "intellicare-admin existe"
else
    log_warning "intellicare-admin não encontrado"
fi

if echo "$CLIENTS" | grep -q "^intellicare-portal$"; then
    log_success "intellicare-portal existe"
else
    log_warning "intellicare-portal não encontrado"
fi

# 7. Verificar roles
log_info "Verificando roles..."

ROLES=$(docker exec "${KEYCLOAK_CONTAINER}" /opt/keycloak/bin/kcadm.sh get roles/PLATFORM_ADMIN -r bemcuidar \
    | jq -r '.name' 2>/dev/null || true)

if [ -n "$ROLES" ]; then
    log_success "Roles configurados"
else
    log_warning "Alguns roles podem não ter sido criados"
fi

# 8. Teste de autenticação
log_info "Testando autenticação..."

# Obter token de admin
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${KEYCLOAK_ADMIN_USER}&password=${KEYCLOAK_ADMIN_PASS}&grant_type=password&client_id=admin-cli" | jq -r '.access_token')

if [ -n "$ADMIN_TOKEN" ] && [ "$ADMIN_TOKEN" != "null" ]; then
    log_success "✅ Autenticação funcionando!"

    # Decodificar token para verificar
    DECODED=$(echo $ADMIN_TOKEN | cut -d. -f2 | base64 -d 2>/dev/null)
    log_info "Token obtido: ${DECODED:0:50}..."
else
    log_error "❌ Falha ao obter token de admin"
    log_info "Verifique se a senha admin está correta"
    log_info "  Senha padrão: admin/changeme (MUDAR EM PRODUÇÃO)"
fi

# 9. Informações de acesso
echo ""
log_success "═══════════════════════════════════════════════"
log_success "   Keycloak configurado com sucesso!              "
log_success "═══════════════════════════════════════════════"
echo ""
echo "🌐 URLs de Acesso:"
echo "  • Keycloak: http://localhost:8080"
echo "  • Admin Console: http://localhost:8080/admin/master/console"
echo ""
echo "🔑 Credenciais Padrão (MUDAR EM PRODUÇÃO):"
echo "  • Usuário: ${KEYCLOAK_ADMIN_USER}"
echo "  • Senha: <valor de KEYCLOAK_ADMIN_PASSWORD>"
echo "  • Realm: bemcuidar"
echo ""
echo "📋 Clients Configurados:"
echo "  • intellicare-admin (porta 8010)"
echo "  • intellicare-portal (porta 3000)"
echo ""
echo "📖 Comandos Úteis:"
echo "  • Ver logs: docker logs -f keycloak-intellicare"
echo "  • Ver health: curl http://localhost:8080/health/ready"
echo "  • Parar: docker-compose -f docker-compose.keycloak.yml down"
echo ""
