#!/bin/bash

# ============================================================================
# SCRIPT DE CONFIGURAÇÃO JITSI + KEYCLOAK - GSI
# ============================================================================
# Servidor: 161.97.141.186
# Keycloak: keycloak.gsi.srv.br
# Realm: bemcuidar
# Client: jitsi-meet (já existe)
# ============================================================================

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        CONFIGURAÇÃO JITSI + KEYCLOAK - GSI.SRV.BR         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# VARIÁVEIS
# ============================================================================

KEYCLOAK_URL="https://keycloak.gsi.srv.br"
KEYCLOAK_REALM="bemcuidar"
KEYCLOAK_CLIENT="jitsi-meet"
JITSI_DOMAIN="meet.gsi.srv.br"
JITSI_PATH="/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

echo -e "${YELLOW}📋 Configurações:${NC}"
echo -e "   Keycloak: ${KEYCLOAK_URL}"
echo -e "   Realm: ${KEYCLOAK_REALM}"
echo -e "   Client: ${KEYCLOAK_CLIENT}"
echo -e "   Jitsi: https://${JITSI_DOMAIN}"
echo -e "   Path: ${JITSI_PATH}"
echo ""

# ============================================================================
# VALIDAÇÕES
# ============================================================================

echo -e "${YELLOW}🔍 Validando ambiente...${NC}"

if [ ! -d "$JITSI_PATH" ]; then
    echo -e "${RED}❌ ERRO: Diretório Jitsi não encontrado: $JITSI_PATH${NC}"
    exit 1
fi

cd "$JITSI_PATH"

if [ ! -f "docker-compose-jitsi.yml" ]; then
    echo -e "${RED}❌ ERRO: docker-compose-jitsi.yml não encontrado${NC}"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ ERRO: .env não encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Ambiente validado${NC}"
echo ""

# ============================================================================
# GERAR JWT SECRET
# ============================================================================

echo -e "${YELLOW}🔐 Gerando JWT Secret...${NC}"
JWT_APP_SECRET=$(openssl rand -hex 32)
echo -e "${GREEN}✅ JWT Secret: ${JWT_APP_SECRET}${NC}"
echo ""

# ============================================================================
# BACKUP
# ============================================================================

echo -e "${YELLOW}💾 Criando backup do .env...${NC}"
BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
cp .env "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup: ${BACKUP_FILE}${NC}"
echo ""

# ============================================================================
# ATUALIZAR .env
# ============================================================================

echo -e "${YELLOW}📝 Atualizando .env...${NC}"

# Remover configurações antigas de JWT/Auth (se existirem)
sed -i '/^ENABLE_AUTH=/d' .env 2>/dev/null || true
sed -i '/^AUTH_TYPE=/d' .env 2>/dev/null || true
sed -i '/^JWT_APP_ID=/d' .env 2>/dev/null || true
sed -i '/^JWT_APP_SECRET=/d' .env 2>/dev/null || true
sed -i '/^TOKEN_AUTH_URL=/d' .env 2>/dev/null || true
sed -i '/^LOGOUT_URL=/d' .env 2>/dev/null || true
sed -i '/^JWT_ACCEPTED_ISSUERS=/d' .env 2>/dev/null || true
sed -i '/^JWT_ACCEPTED_AUDIENCES=/d' .env 2>/dev/null || true
sed -i '/^JWT_ASAP_KEYSERVER=/d' .env 2>/dev/null || true
sed -i '/^ENABLE_GUESTS=/d' .env 2>/dev/null || true

# Adicionar configurações Keycloak
cat >> .env << EOF

# ============================================================================
# KEYCLOAK SSO CONFIGURATION
# Configurado automaticamente em $(date)
# ============================================================================

# Enable JWT authentication
ENABLE_AUTH=1
AUTH_TYPE=jwt

# JWT Token Configuration
JWT_APP_ID=${KEYCLOAK_CLIENT}
JWT_APP_SECRET=${JWT_APP_SECRET}

# Keycloak OAuth2 URLs
TOKEN_AUTH_URL=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth
LOGOUT_URL=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout

# JWT Validation
JWT_ACCEPTED_ISSUERS=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}
JWT_ACCEPTED_AUDIENCES=${KEYCLOAK_CLIENT}
JWT_ASAP_KEYSERVER=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs

# Disable anonymous access (force Keycloak login)
ENABLE_GUESTS=0
EOF

echo -e "${GREEN}✅ .env atualizado com sucesso${NC}"
echo ""

# ============================================================================
# REINICIAR CONTAINERS
# ============================================================================

echo -e "${YELLOW}🔄 Reiniciando containers Jitsi...${NC}"

echo -e "   Parando containers..."
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down

echo -e "   Aguardando 5 segundos..."
sleep 5

echo -e "   Iniciando containers..."
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

echo -e "${GREEN}✅ Containers reiniciados${NC}"
echo ""

# ============================================================================
# AGUARDAR INICIALIZAÇÃO
# ============================================================================

echo -e "${YELLOW}⏳ Aguardando serviços iniciarem (30 segundos)...${NC}"
for i in {30..1}; do
    echo -ne "   ${i}s restantes...\r"
    sleep 1
done
echo -e "${GREEN}✅ Serviços iniciados${NC}"
echo ""

# ============================================================================
# VERIFICAR STATUS
# ============================================================================

echo -e "${YELLOW}📊 Status dos containers:${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps
echo ""

# ============================================================================
# SALVAR CONFIGURAÇÕES
# ============================================================================

CONFIG_FILE="jitsi-keycloak-config-$(date +%Y%m%d_%H%M%S).txt"

cat > "$CONFIG_FILE" << EOF
╔════════════════════════════════════════════════════════════╗
║     JITSI + KEYCLOAK CONFIGURATION - GSI.SRV.BR            ║
╚════════════════════════════════════════════════════════════╝

Data: $(date)
Servidor: 161.97.141.186

KEYCLOAK CONFIGURATION
======================
URL: ${KEYCLOAK_URL}
Realm: ${KEYCLOAK_REALM}
Client ID: ${KEYCLOAK_CLIENT}

JITSI CONFIGURATION
===================
Domain: https://${JITSI_DOMAIN}
Path: ${JITSI_PATH}

JWT CONFIGURATION
=================
JWT_APP_ID: ${KEYCLOAK_CLIENT}
JWT_APP_SECRET: ${JWT_APP_SECRET}

KEYCLOAK URLS
=============
Auth URL: ${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth
Logout URL: ${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout
Certs URL: ${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs

KEYCLOAK CLIENT SETTINGS (Verificar)
=====================================
Client ID: ${KEYCLOAK_CLIENT}
Client Protocol: openid-connect
Access Type: public
Standard Flow Enabled: ON
Implicit Flow Enabled: ON
Direct Access Grants Enabled: ON
Valid Redirect URIs: https://${JITSI_DOMAIN}/*
Web Origins: https://${JITSI_DOMAIN}
Base URL: https://${JITSI_DOMAIN}

REQUIRED MAPPERS (Criar se não existirem)
==========================================
1. username
   - Mapper Type: User Property
   - Property: username
   - Token Claim Name: username
   - Add to ID/Access/Userinfo: ON

2. email
   - Mapper Type: User Property
   - Property: email
   - Token Claim Name: email
   - Add to ID/Access/Userinfo: ON

3. name
   - Mapper Type: User Property
   - Property: firstName
   - Token Claim Name: name
   - Add to ID/Access/Userinfo: ON

BACKUP
======
.env original: ${BACKUP_FILE}

TESTING
=======
1. Acesse: https://${JITSI_DOMAIN}
2. Crie uma sala
3. Deve redirecionar para: ${KEYCLOAK_URL}
4. Faça login com usuário do realm '${KEYCLOAK_REALM}'
5. Deve voltar para Jitsi e entrar na sala

TROUBLESHOOTING
===============
Ver logs:
  docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f

Ver logs do web:
  docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f web

Reiniciar:
  docker compose -f docker-compose-jitsi.yml -p jitsi-meet restart

Reverter configuração:
  cp ${BACKUP_FILE} .env
  docker compose -f docker-compose-jitsi.yml -p jitsi-meet restart
EOF

echo -e "${GREEN}✅ Configurações salvas em: ${CONFIG_FILE}${NC}"
echo ""

# ============================================================================
# RESUMO FINAL
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  CONFIGURAÇÃO COMPLETA! ✅                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Jitsi configurado para autenticação via Keycloak${NC}"
echo ""
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo ""
echo -e "${YELLOW}1️⃣  VERIFICAR KEYCLOAK CLIENT${NC}"
echo -e "   Acesse: ${KEYCLOAK_URL}/admin"
echo -e "   Realm: ${KEYCLOAK_REALM}"
echo -e "   Clients → ${KEYCLOAK_CLIENT} → Settings"
echo ""
echo -e "   ${GREEN}Verificar:${NC}"
echo -e "   ✓ Valid Redirect URIs: https://${JITSI_DOMAIN}/*"
echo -e "   ✓ Web Origins: https://${JITSI_DOMAIN}"
echo -e "   ✓ Access Type: public"
echo ""
echo -e "${YELLOW}2️⃣  VERIFICAR MAPPERS${NC}"
echo -e "   Clients → ${KEYCLOAK_CLIENT} → Mappers"
echo ""
echo -e "   ${GREEN}Deve ter:${NC}"
echo -e "   ✓ username (User Property → username)"
echo -e "   ✓ email (User Property → email)"
echo -e "   ✓ name (User Property → firstName)"
echo ""
echo -e "${YELLOW}3️⃣  TESTAR${NC}"
echo -e "   1. Acesse: ${GREEN}https://${JITSI_DOMAIN}${NC}"
echo -e "   2. Crie uma sala (ex: 'teste')"
echo -e "   3. ${GREEN}Deve redirecionar para Keycloak${NC}"
echo -e "   4. Faça login com usuário do realm '${KEYCLOAK_REALM}'"
echo -e "   5. ${GREEN}Deve voltar para Jitsi automaticamente${NC}"
echo ""
echo -e "${YELLOW}📊 MONITORAMENTO:${NC}"
echo -e "   Ver logs: ${GREEN}docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f${NC}"
echo ""
echo -e "${YELLOW}💾 BACKUP:${NC}"
echo -e "   .env original: ${GREEN}${BACKUP_FILE}${NC}"
echo -e "   Configurações: ${GREEN}${CONFIG_FILE}${NC}"
echo ""
echo -e "${YELLOW}🔄 REVERTER (se necessário):${NC}"
echo -e "   ${GREEN}cp ${BACKUP_FILE} .env${NC}"
echo -e "   ${GREEN}docker compose -f docker-compose-jitsi.yml -p jitsi-meet restart${NC}"
echo ""

