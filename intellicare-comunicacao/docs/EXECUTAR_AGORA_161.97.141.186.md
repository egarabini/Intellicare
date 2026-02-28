# ⚡ EXECUTAR AGORA - SERVIDOR 161.97.141.186

---

## 🎯 CONFIGURAÇÃO JITSI + KEYCLOAK - COMANDOS PRONTOS

**Servidor**: 161.97.141.186  
**Keycloak**: https://keycloak.gsi.srv.br  
**Realm**: bemcuidar  
**Client**: jitsi-meet (já existe)  
**Jitsi**: https://meet.gsi.srv.br

---

## ⚡ OPÇÃO 1: SCRIPT AUTOMATIZADO (RECOMENDADO)

### **Copie e cole estes comandos no seu terminal:**

```bash
# 1. Conectar ao servidor
ssh root@161.97.141.186

# 2. Navegar para o diretório Jitsi
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/

# 3. Criar o script
cat > configure-jitsi-keycloak-gsi.sh << 'SCRIPT_EOF'
#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        CONFIGURAÇÃO JITSI + KEYCLOAK - GSI.SRV.BR         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

KEYCLOAK_URL="https://keycloak.gsi.srv.br"
KEYCLOAK_REALM="bemcuidar"
KEYCLOAK_CLIENT="jitsi-meet"
JITSI_DOMAIN="meet.gsi.srv.br"
JITSI_PATH="/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

echo -e "${YELLOW}📋 Configurações:${NC}"
echo "   Keycloak: ${KEYCLOAK_URL}"
echo "   Realm: ${KEYCLOAK_REALM}"
echo "   Client: ${KEYCLOAK_CLIENT}"
echo "   Jitsi: https://${JITSI_DOMAIN}"
echo ""

cd "$JITSI_PATH"

echo -e "${YELLOW}🔐 Gerando JWT Secret...${NC}"
JWT_APP_SECRET=$(openssl rand -hex 32)
echo -e "${GREEN}✅ JWT Secret: ${JWT_APP_SECRET}${NC}"
echo ""

echo -e "${YELLOW}💾 Criando backup...${NC}"
BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
cp .env "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup: ${BACKUP_FILE}${NC}"
echo ""

echo -e "${YELLOW}📝 Atualizando .env...${NC}"

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

cat >> .env << EOF

# ============================================================================
# KEYCLOAK SSO - Configurado em $(date)
# ============================================================================
ENABLE_AUTH=1
AUTH_TYPE=jwt
JWT_APP_ID=${KEYCLOAK_CLIENT}
JWT_APP_SECRET=${JWT_APP_SECRET}
TOKEN_AUTH_URL=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth
LOGOUT_URL=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout
JWT_ACCEPTED_ISSUERS=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}
JWT_ACCEPTED_AUDIENCES=${KEYCLOAK_CLIENT}
JWT_ASAP_KEYSERVER=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs
ENABLE_GUESTS=0
EOF

echo -e "${GREEN}✅ .env atualizado${NC}"
echo ""

echo -e "${YELLOW}🔄 Reiniciando Jitsi...${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down
sleep 5
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

echo -e "${GREEN}✅ Containers reiniciados${NC}"
echo ""

echo -e "${YELLOW}⏳ Aguardando 30s...${NC}"
sleep 30

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  CONFIGURAÇÃO COMPLETA! ✅                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}JWT Secret: ${JWT_APP_SECRET}${NC}"
echo -e "${GREEN}Backup: ${BACKUP_FILE}${NC}"
echo ""
echo -e "${YELLOW}PRÓXIMOS PASSOS:${NC}"
echo "1. Verificar Keycloak client em: ${KEYCLOAK_URL}/admin"
echo "2. Testar em: https://${JITSI_DOMAIN}"
echo ""
SCRIPT_EOF

# 4. Dar permissão de execução
chmod +x configure-jitsi-keycloak-gsi.sh

# 5. Executar o script
./configure-jitsi-keycloak-gsi.sh
```

**PRONTO!** O script faz tudo automaticamente! ✅

---

## ⚡ OPÇÃO 2: COMANDOS MANUAIS

Se preferir fazer passo a passo:

```bash
# 1. Conectar
ssh root@161.97.141.186

# 2. Navegar
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/

# 3. Gerar JWT Secret
JWT_SECRET=$(openssl rand -hex 32)
echo "JWT Secret: $JWT_SECRET"

# 4. Backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 5. Adicionar configurações ao .env
cat >> .env << EOF

# KEYCLOAK SSO
ENABLE_AUTH=1
AUTH_TYPE=jwt
JWT_APP_ID=jitsi-meet
JWT_APP_SECRET=$JWT_SECRET
TOKEN_AUTH_URL=https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth
LOGOUT_URL=https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/logout
JWT_ACCEPTED_ISSUERS=https://keycloak.gsi.srv.br/realms/bemcuidar
JWT_ACCEPTED_AUDIENCES=jitsi-meet
JWT_ASAP_KEYSERVER=https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/certs
ENABLE_GUESTS=0
EOF

# 6. Reiniciar
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

# 7. Ver logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f
```

---

## 🔐 CONFIGURAR KEYCLOAK (VERIFICAR)

### **1. Acessar Keycloak Admin**

```
URL: https://keycloak.gsi.srv.br/admin
Realm: bemcuidar
```

### **2. Verificar Client `jitsi-meet`**

**Clients → jitsi-meet → Settings**

Verificar se está configurado:
- ✅ Client Protocol: `openid-connect`
- ✅ Access Type: `public`
- ✅ Standard Flow Enabled: `ON`
- ✅ Implicit Flow Enabled: `ON`
- ✅ Valid Redirect URIs: `https://meet.gsi.srv.br/*`
- ✅ Web Origins: `https://meet.gsi.srv.br`

### **3. Verificar/Criar Mappers**

**Clients → jitsi-meet → Mappers**

Deve ter pelo menos 3 mappers:

**Mapper 1: username**
- Mapper Type: `User Property`
- Property: `username`
- Token Claim Name: `username`
- Add to ID/Access/Userinfo: `ON`

**Mapper 2: email**
- Mapper Type: `User Property`
- Property: `email`
- Token Claim Name: `email`
- Add to ID/Access/Userinfo: `ON`

**Mapper 3: name**
- Mapper Type: `User Property`
- Property: `firstName`
- Token Claim Name: `name`
- Add to ID/Access/Userinfo: `ON`

---

## ✅ TESTAR

### **1. Acessar Jitsi**

```
https://meet.gsi.srv.br
```

### **2. Criar uma sala**

- Digite: `teste`
- Clique em "Go" ou "Iniciar"

### **3. Verificar redirecionamento**

- **Deve redirecionar para**: `https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/auth...`

### **4. Fazer login**

- Use um usuário do realm `bemcuidar`
- Faça login

### **5. Verificar retorno**

- **Deve voltar para**: `https://meet.gsi.srv.br/teste`
- **Deve entrar na sala automaticamente**
- **Nome do usuário deve aparecer**

---

## 🛠️ TROUBLESHOOTING

### **Não redireciona para Keycloak**

```bash
# Ver logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs web | grep -i auth

# Verificar .env
cat .env | grep -A 10 "KEYCLOAK"
```

### **Erro "Invalid token"**

```bash
# Verificar JWT_APP_SECRET
cat .env | grep JWT_APP_SECRET
```

### **Erro CORS**

- Verificar Web Origins no Keycloak: `https://meet.gsi.srv.br`

### **Reverter configuração**

```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/
cp .env.backup.* .env
docker compose -f docker-compose-jitsi.yml -p jitsi-meet restart
```

---

## 📊 COMANDOS ÚTEIS

```bash
# Status
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps

# Logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f

# Logs apenas web
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f web

# Reiniciar
docker compose -f docker-compose-jitsi.yml -p jitsi-meet restart

# Parar
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down

# Iniciar
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d
```

---

## 🎯 RESUMO

1. ✅ Execute o script da **OPÇÃO 1** (recomendado)
2. ✅ Verifique configurações no Keycloak
3. ✅ Teste em https://meet.gsi.srv.br
4. ✅ Deve redirecionar para Keycloak
5. ✅ Faça login
6. ✅ Deve voltar para Jitsi

---

**EXECUTE AGORA E ME AVISE SE DER ALGUM ERRO!** 🚀

