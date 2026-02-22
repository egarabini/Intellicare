# 🔐 INTEGRAÇÃO JITSI + KEYCLOAK - SERVIDOR 161.97.141.186

---

## 📋 INFORMAÇÕES DO AMBIENTE

**Servidor**: 161.97.141.186  
**Usuário**: root  
**Sistema**: Ubuntu  
**Domínio Jitsi**: meet.gsi.srv.br  
**Keycloak Realm**: bemcuidar  
**Keycloak Client**: jitsi-meet  
**Caminho**: /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/

---

## 🎯 ETAPA 1: CONFIGURAR KEYCLOAK CLIENT

### **1.1. Acessar Keycloak Admin Console**

```
URL: https://SEU_KEYCLOAK_URL/admin
Realm: bemcuidar
```

### **1.2. Configurar Client `jitsi-meet`**

**Settings**:
- Client ID: `jitsi-meet`
- Client Protocol: `openid-connect`
- Access Type: `public`
- Standard Flow Enabled: `ON`
- Implicit Flow Enabled: `ON`
- Direct Access Grants Enabled: `ON`
- Valid Redirect URIs: `https://meet.gsi.srv.br/*`
- Web Origins: `https://meet.gsi.srv.br`
- Base URL: `https://meet.gsi.srv.br`

**Mappers** (criar os seguintes):

1. **Mapper: username**
   - Name: `username`
   - Mapper Type: `User Property`
   - Property: `username`
   - Token Claim Name: `username`
   - Claim JSON Type: `String`
   - Add to ID token: `ON`
   - Add to access token: `ON`
   - Add to userinfo: `ON`

2. **Mapper: email**
   - Name: `email`
   - Mapper Type: `User Property`
   - Property: `email`
   - Token Claim Name: `email`
   - Claim JSON Type: `String`
   - Add to ID token: `ON`
   - Add to access token: `ON`
   - Add to userinfo: `ON`

3. **Mapper: name**
   - Name: `name`
   - Mapper Type: `User Property`
   - Property: `firstName`
   - Token Claim Name: `name`
   - Claim JSON Type: `String`
   - Add to ID token: `ON`
   - Add to access token: `ON`
   - Add to userinfo: `ON`

4. **Mapper: avatar (opcional)**
   - Name: `avatar`
   - Mapper Type: `User Attribute`
   - User Attribute: `avatar`
   - Token Claim Name: `avatar`
   - Claim JSON Type: `String`
   - Add to ID token: `ON`
   - Add to access token: `ON`

### **1.3. Obter Informações do Keycloak**

Você vai precisar:
- **Keycloak URL**: https://SEU_KEYCLOAK_URL
- **Realm**: bemcuidar
- **Client ID**: jitsi-meet
- **Client Secret**: (se configurou como confidential)

---

## 🎯 ETAPA 2: CONFIGURAR JITSI PARA KEYCLOAK

### **2.1. Atualizar .env**

Conecte ao servidor e edite o .env:

```bash
ssh root@161.97.141.186
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/
nano .env
```

**Adicione/Modifique as seguintes variáveis**:

```bash
# ============================================================================
# KEYCLOAK SSO CONFIGURATION
# ============================================================================

# Habilitar autenticação
ENABLE_AUTH=1
AUTH_TYPE=jwt

# Token Configuration
JWT_APP_ID=jitsi-meet
JWT_APP_SECRET=SEU_SECRET_AQUI_GERE_UM_RANDOM

# Keycloak URLs
TOKEN_AUTH_URL=https://SEU_KEYCLOAK_URL/realms/bemcuidar/protocol/openid-connect/auth
LOGOUT_URL=https://SEU_KEYCLOAK_URL/realms/bemcuidar/protocol/openid-connect/logout

# JWT Issuer (Keycloak)
JWT_ACCEPTED_ISSUERS=https://SEU_KEYCLOAK_URL/realms/bemcuidar

# JWT Audience
JWT_ACCEPTED_AUDIENCES=jitsi-meet

# JWT Algorithm
JWT_ASAP_KEYSERVER=https://SEU_KEYCLOAK_URL/realms/bemcuidar/protocol/openid-connect/certs

# Disable guests (force login)
ENABLE_GUESTS=0

# ============================================================================
# EXISTING CONFIGURATION (keep as is)
# ============================================================================
PUBLIC_URL=https://meet.gsi.srv.br/
XMPP_DOMAIN=meet.gsi.srv.br
XMPP_AUTH_DOMAIN=auth.meet.gsi.srv.br
XMPP_GUEST_DOMAIN=guest.meet.gsi.srv.br
XMPP_MUC_DOMAIN=muc.meet.gsi.srv.br
XMPP_INTERNAL_MUC_DOMAIN=internal-muc.meet.gsi.srv.br
XMPP_SERVER=xmpp.meet.gsi.srv.br

# Passwords (já existentes)
JICOFO_AUTH_PASSWORD=SEU_PASSWORD_EXISTENTE
JVB_AUTH_PASSWORD=SEU_PASSWORD_EXISTENTE
JICOFO_COMPONENT_SECRET=SEU_SECRET_EXISTENTE

# Docker
DOCKER_HOST_ADDRESS=161.97.141.186
JVB_PORT=10000
TZ=America/Sao_Paulo
RESTART_POLICY=unless-stopped

# Config path
CONFIG=/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/.jitsi-meet-cfg
```

### **2.2. Gerar JWT_APP_SECRET**

```bash
# Gerar secret aleatório
openssl rand -hex 32
```

Copie o resultado e use como `JWT_APP_SECRET` no .env

---

## 🎯 ETAPA 3: CONFIGURAR JITSI WEB (config.js)

### **3.1. Editar config.js**

```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/.jitsi-meet-cfg/web
nano config.js
```

**Adicione dentro de `config = {`**:

```javascript
// Keycloak SSO Configuration
enableUserRolesBasedOnToken: true,
tokenAuthUrl: 'https://SEU_KEYCLOAK_URL/realms/bemcuidar/protocol/openid-connect/auth',
tokenLogoutUrl: 'https://SEU_KEYCLOAK_URL/realms/bemcuidar/protocol/openid-connect/logout',

// JWT Configuration
jwt: {
    enabled: true,
    id: 'jitsi-meet',
    secret: 'SEU_JWT_APP_SECRET_AQUI',
    issuer: 'https://SEU_KEYCLOAK_URL/realms/bemcuidar',
    audience: 'jitsi-meet',
    keyserver: 'https://SEU_KEYCLOAK_URL/realms/bemcuidar/protocol/openid-connect/certs'
},

// Disable anonymous/guest access
enableInsecureRoomNameWarning: true,
requireDisplayName: true,
```

---

## 🎯 ETAPA 4: REINICIAR JITSI

```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/

# Parar containers
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down

# Limpar configurações antigas (CUIDADO!)
# rm -rf .jitsi-meet-cfg/*

# Iniciar novamente
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

# Ver logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f
```

---

## ✅ ETAPA 5: TESTAR

1. Acesse: https://meet.gsi.srv.br
2. Tente criar uma sala
3. Deve redirecionar para Keycloak login
4. Faça login com usuário do realm `bemcuidar`
5. Deve voltar para Jitsi e entrar na sala

---

## 🛠️ TROUBLESHOOTING

### **Erro: "Room locked"**
- Verificar `ENABLE_GUESTS=0` no .env
- Verificar `ENABLE_AUTH=1` no .env

### **Erro: "Invalid token"**
- Verificar JWT_APP_SECRET igual em .env e config.js
- Verificar JWT_ACCEPTED_ISSUERS correto
- Verificar certificados Keycloak válidos

### **Não redireciona para Keycloak**
- Verificar tokenAuthUrl correto
- Verificar Valid Redirect URIs no Keycloak
- Limpar cache do navegador

---

## 📝 COMANDOS ÚTEIS

```bash
# Ver logs do Jitsi Web
docker logs jitsi-meet-web-1 -f

# Ver logs do Prosody
docker logs jitsi-meet-prosody-1 -f

# Reiniciar apenas web
docker compose -f docker-compose-jitsi.yml -p jitsi-meet restart web

# Verificar configuração
docker exec jitsi-meet-web-1 cat /config/config.js | grep -A 10 "jwt"
```

---

**IMPORTANTE**: Substitua `SEU_KEYCLOAK_URL` pela URL real do seu Keycloak!


