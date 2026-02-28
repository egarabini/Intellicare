#!/bin/bash

# ============================================================================
# SCRIPT DE CONFIGURAÇÃO JITSI + KEYCLOAK
# ============================================================================
# Servidor: 161.97.141.186
# Usuário: root
# Realm: bemcuidar
# Client: jitsi-meet
# ============================================================================

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CONFIGURAÇÃO JITSI + KEYCLOAK - SERVIDOR 161.97.141.186 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# VARIÁVEIS - CONFIGURE AQUI!
# ============================================================================

# Keycloak Configuration
KEYCLOAK_URL="https://SEU_KEYCLOAK_URL"  # ⚠️ ALTERE AQUI!
KEYCLOAK_REALM="bemcuidar"
KEYCLOAK_CLIENT="jitsi-meet"

# Jitsi Configuration
JITSI_DOMAIN="meet.gsi.srv.br"
JITSI_PATH="/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

# ============================================================================
# VALIDAÇÕES
# ============================================================================

echo -e "${YELLOW}📋 Validando configurações...${NC}"

if [ "$KEYCLOAK_URL" == "https://SEU_KEYCLOAK_URL" ]; then
    echo -e "${RED}❌ ERRO: Configure KEYCLOAK_URL no script!${NC}"
    echo -e "${YELLOW}   Edite a linha 28 do script com a URL real do Keycloak${NC}"
    exit 1
fi

if [ ! -d "$JITSI_PATH" ]; then
    echo -e "${RED}❌ ERRO: Diretório Jitsi não encontrado: $JITSI_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configurações validadas${NC}"
echo ""

# ============================================================================
# GERAR JWT SECRET
# ============================================================================

echo -e "${YELLOW}🔐 Gerando JWT Secret...${NC}"
JWT_APP_SECRET=$(openssl rand -hex 32)
echo -e "${GREEN}✅ JWT Secret gerado: ${JWT_APP_SECRET}${NC}"
echo ""

# ============================================================================
# BACKUP DO .env ATUAL
# ============================================================================

echo -e "${YELLOW}💾 Fazendo backup do .env atual...${NC}"
cd "$JITSI_PATH"

if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup criado${NC}"
else
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado, será criado${NC}"
fi
echo ""

# ============================================================================
# ATUALIZAR .env
# ============================================================================

echo -e "${YELLOW}📝 Atualizando .env com configurações Keycloak...${NC}"

# Remover configurações antigas de JWT (se existirem)
sed -i '/^ENABLE_AUTH=/d' .env 2>/dev/null || true
sed -i '/^AUTH_TYPE=/d' .env 2>/dev/null || true
sed -i '/^JWT_APP_ID=/d' .env 2>/dev/null || true
sed -i '/^JWT_APP_SECRET=/d' .env 2>/dev/null || true
sed -i '/^TOKEN_AUTH_URL=/d' .env 2>/dev/null || true
sed -i '/^LOGOUT_URL=/d' .env 2>/dev/null || true
sed -i '/^JWT_ACCEPTED_ISSUERS=/d' .env 2>/dev/null || true
sed -i '/^JWT_ACCEPTED_AUDIENCES=/d' .env 2>/dev/null || true
sed -i '/^JWT_ASAP_KEYSERVER=/d' .env 2>/dev/null || true

# Adicionar novas configurações
cat >> .env << EOF

# ============================================================================
# KEYCLOAK SSO CONFIGURATION (Added by configure-jitsi-keycloak.sh)
# ============================================================================

# Enable authentication
ENABLE_AUTH=1
AUTH_TYPE=jwt

# Token Configuration
JWT_APP_ID=${KEYCLOAK_CLIENT}
JWT_APP_SECRET=${JWT_APP_SECRET}

# Keycloak URLs
TOKEN_AUTH_URL=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth
LOGOUT_URL=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout

# JWT Issuer (Keycloak)
JWT_ACCEPTED_ISSUERS=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}

# JWT Audience
JWT_ACCEPTED_AUDIENCES=${KEYCLOAK_CLIENT}

# JWT Algorithm
JWT_ASAP_KEYSERVER=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs

# Disable guests (force login)
ENABLE_GUESTS=0
EOF

echo -e "${GREEN}✅ .env atualizado${NC}"
echo ""

# ============================================================================
# REINICIAR JITSI
# ============================================================================

echo -e "${YELLOW}🔄 Reiniciando containers Jitsi...${NC}"

docker compose -f docker-compose-jitsi.yml -p jitsi-meet down
sleep 3
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

echo -e "${GREEN}✅ Containers reiniciados${NC}"
echo ""

# ============================================================================
# AGUARDAR SERVIÇOS
# ============================================================================

echo -e "${YELLOW}⏳ Aguardando serviços iniciarem (30s)...${NC}"
sleep 30

# ============================================================================
# VERIFICAR STATUS
# ============================================================================

echo -e "${YELLOW}📊 Verificando status dos containers...${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps
echo ""

# ============================================================================
# RESUMO
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    CONFIGURAÇÃO COMPLETA                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Jitsi configurado para usar Keycloak SSO${NC}"
echo ""
echo -e "${YELLOW}📋 INFORMAÇÕES IMPORTANTES:${NC}"
echo -e "   Keycloak URL:    ${KEYCLOAK_URL}"
echo -e "   Realm:           ${KEYCLOAK_REALM}"
echo -e "   Client ID:       ${KEYCLOAK_CLIENT}"
echo -e "   JWT Secret:      ${JWT_APP_SECRET}"
echo ""
echo -e "${YELLOW}🔐 CONFIGURAR NO KEYCLOAK:${NC}"
echo -e "   1. Acesse: ${KEYCLOAK_URL}/admin"
echo -e "   2. Realm: ${KEYCLOAK_REALM}"
echo -e "   3. Client: ${KEYCLOAK_CLIENT}"
echo -e "   4. Valid Redirect URIs: https://${JITSI_DOMAIN}/*"
echo -e "   5. Web Origins: https://${JITSI_DOMAIN}"
echo ""
echo -e "${YELLOW}✅ TESTAR:${NC}"
echo -e "   1. Acesse: https://${JITSI_DOMAIN}"
echo -e "   2. Crie uma sala"
echo -e "   3. Deve redirecionar para Keycloak"
echo -e "   4. Faça login"
echo -e "   5. Deve voltar para Jitsi"
echo ""
echo -e "${YELLOW}📝 BACKUP:${NC}"
echo -e "   .env original salvo em: .env.backup.*"
echo ""
echo -e "${YELLOW}📊 VER LOGS:${NC}"
echo -e "   docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f"
echo ""

# ============================================================================
# SALVAR INFORMAÇÕES
# ============================================================================

cat > jitsi-keycloak-config.txt << EOF
JITSI + KEYCLOAK CONFIGURATION
================================
Date: $(date)
Server: 161.97.141.186

Keycloak Configuration:
-----------------------
URL: ${KEYCLOAK_URL}
Realm: ${KEYCLOAK_REALM}
Client ID: ${KEYCLOAK_CLIENT}

JWT Configuration:
------------------
JWT_APP_SECRET: ${JWT_APP_SECRET}

Jitsi Configuration:
--------------------
Domain: ${JITSI_DOMAIN}
Path: ${JITSI_PATH}

Token URLs:
-----------
Auth: ${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth
Logout: ${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout
Certs: ${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs

Keycloak Client Settings:
-------------------------
- Client ID: ${KEYCLOAK_CLIENT}
- Client Protocol: openid-connect
- Access Type: public
- Valid Redirect URIs: https://${JITSI_DOMAIN}/*
- Web Origins: https://${JITSI_DOMAIN}

Required Mappers:
-----------------
1. username (User Property → username)
2. email (User Property → email)
3. name (User Property → firstName)
EOF

echo -e "${GREEN}✅ Configurações salvas em: jitsi-keycloak-config.txt${NC}"
echo ""

