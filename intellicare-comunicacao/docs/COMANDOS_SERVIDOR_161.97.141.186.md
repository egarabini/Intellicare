# 🚀 COMANDOS PARA SERVIDOR 161.97.141.186

---

## ⚡ EXECUÇÃO RÁPIDA

### **ANTES DE COMEÇAR**: Me informe a URL do Keycloak!

Exemplo: `https://keycloak.gsi.srv.br` ou `https://auth.gsi.srv.br`

---

## 📝 PASSO A PASSO

### **1. Conectar ao Servidor**

```bash
ssh root@161.97.141.186
```

### **2. Navegar para o diretório Jitsi**

```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/
```

### **3. Fazer backup do .env atual**

```bash
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

### **4. Gerar JWT Secret**

```bash
JWT_SECRET=$(openssl rand -hex 32)
echo "JWT Secret gerado: $JWT_SECRET"
```

### **5. Editar .env**

```bash
nano .env
```

**Adicione no FINAL do arquivo**:

```bash
# ============================================================================
# KEYCLOAK SSO CONFIGURATION
# ============================================================================

# Enable authentication
ENABLE_AUTH=1
AUTH_TYPE=jwt

# Token Configuration
JWT_APP_ID=jitsi-meet
JWT_APP_SECRET=COLE_O_JWT_SECRET_AQUI

# Keycloak URLs (⚠️ ALTERE A URL DO KEYCLOAK!)
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
```

**Salvar**: `Ctrl+X`, `Y`, `Enter`

### **6. Reiniciar Jitsi**

```bash
# Parar containers
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down

# Iniciar novamente
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

# Ver logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f
```

---

## 🔐 CONFIGURAR KEYCLOAK

### **1. Acessar Keycloak Admin**

```
URL: https://SEU_KEYCLOAK_URL/admin
Realm: bemcuidar
```

### **2. Configurar Client `jitsi-meet`**

**Se o client já existe**:
- Clients → jitsi-meet → Settings

**Se precisa criar**:
- Clients → Create Client

**Configurações**:
```
Client ID: jitsi-meet
Client Protocol: openid-connect
Access Type: public
Standard Flow Enabled: ON
Implicit Flow Enabled: ON
Direct Access Grants Enabled: ON
Valid Redirect URIs: https://meet.gsi.srv.br/*
Web Origins: https://meet.gsi.srv.br
Base URL: https://meet.gsi.srv.br
```

### **3. Criar Mappers**

**Clients → jitsi-meet → Mappers → Create**

**Mapper 1: username**
```
Name: username
Mapper Type: User Property
Property: username
Token Claim Name: username
Claim JSON Type: String
Add to ID token: ON
Add to access token: ON
Add to userinfo: ON
```

**Mapper 2: email**
```
Name: email
Mapper Type: User Property
Property: email
Token Claim Name: email
Claim JSON Type: String
Add to ID token: ON
Add to access token: ON
Add to userinfo: ON
```

**Mapper 3: name**
```
Name: name
Mapper Type: User Property
Property: firstName
Token Claim Name: name
Claim JSON Type: String
Add to ID token: ON
Add to access token: ON
Add to userinfo: ON
```

---

## ✅ TESTAR

### **1. Acessar Jitsi**

```
https://meet.gsi.srv.br
```

### **2. Criar uma sala**

- Digite um nome de sala
- Clique em "Go"
- **Deve redirecionar para Keycloak**

### **3. Fazer login no Keycloak**

- Use um usuário do realm `bemcuidar`
- Faça login

### **4. Verificar**

- Deve voltar para Jitsi
- Deve entrar na sala automaticamente
- Nome do usuário deve aparecer

---

## 🛠️ TROUBLESHOOTING

### **Problema: Não redireciona para Keycloak**

```bash
# Verificar .env
cat .env | grep -A 15 "KEYCLOAK"

# Verificar logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs web | grep -i auth
```

### **Problema: "Invalid token"**

```bash
# Verificar JWT_APP_SECRET
cat .env | grep JWT_APP_SECRET

# Deve ser o mesmo que foi gerado
```

### **Problema: "CORS error"**

- Verificar Web Origins no Keycloak
- Deve ser: `https://meet.gsi.srv.br`

### **Ver logs em tempo real**

```bash
# Todos os containers
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f

# Apenas web
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f web

# Apenas prosody
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs -f prosody
```

---

## 📊 COMANDOS ÚTEIS

```bash
# Status dos containers
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps

# Reiniciar apenas web
docker compose -f docker-compose-jitsi.yml -p jitsi-meet restart web

# Parar tudo
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down

# Iniciar tudo
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

# Ver uso de recursos
docker stats

# Limpar logs
docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs --tail=0 -f
```

---

## 🔄 REVERTER CONFIGURAÇÃO

Se algo der errado:

```bash
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb/

# Restaurar backup
cp .env.backup.XXXXXXXX_XXXXXX .env

# Reiniciar
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d
```

---

## 📞 PRÓXIMOS PASSOS

Após configurar Jitsi + Keycloak:

1. ✅ Testar login com vários usuários
2. ✅ Testar criação de salas
3. ✅ Testar videoconferência
4. ⏳ Configurar Rocket.Chat (se necessário)
5. ⏳ Integrar com outros módulos IntelliCare

---

**ME INFORME A URL DO KEYCLOAK E EU CRIO OS COMANDOS EXATOS!** 🚀

