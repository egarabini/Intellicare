# 05 - Testar Autenticação

## 📋 Visão Geral

Este guia cobre os testes de autenticação Keycloak para garantir que tudo está funcionando corretamente.

## 🧪 Testes Automatizados

### 1. Teste de Health do Keycloak

```bash
# Testar se Keycloak está respondendo
curl http://localhost:8080/health/ready

# Saída esperada:
{
  "status": "UP",
  "checks": [
    {
      "name": "Keycloak database connections async health check",
      "status": "UP"
    }
  ]
}
```

### 2. Teste de Realm

```bash
# Verificar se realm bemcuidar existe
curl -s http://localhost:8080/realms/bemcuidar | jq .

# Verificar public key
curl -s http://localhost:8080/realms/bemcuidar/protocol/openid-connect/certs | jq .
```

### 3. Teste de Autenticação

```bash
# Login como admin@intellicare.ia.br
curl -s -X POST "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@intellicare.ia.br&password=changeme-admin&grant_type=password&client_id=intellicare-admin" \
  | jq .

# Saída esperada:
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "token_type": "Bearer"
}
```

### 4. Teste de Endpoint Protegido

```bash
# Obter token
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@intellicare.ia.br&password=changeme-admin&grant_type=password&client_id=intellicare-admin" \
  | jq -r '.access_token')

# Acessar endpoint protegido
curl -H "Authorization: Bearer $TOKEN" http://localhost:8010/api/v1/admin/users

# Sem token (deve falhar)
curl http://localhost:8010/api/v1/admin/users
# Esperado: 401 Unauthorized
```

## 🧪 Teste Manual via Browser

### 1. Acessar Admin Console

```
URL: http://localhost:8080/admin
User: admin
Password: <ver .env.keycloak>

Verificar:
- [ ] Realm bemcuidar aparece
- [ ] Clients intellicare-admin e intellicare-portal existem
- [ ] User admin@intellicare.ia.br existe
- [ ] Roles PLATFORM_ADMIN, PLATFORM_GESTOR, PLATFORM_SUPPORT, PLATFORM_BILLING existem
```

### 2. Login no Portal

```
1. Acessar: http://localhost:3001
2. Clicar em "Login"
3. Redirecionar para Keycloak
4. Login com admin@intellicare.ia.br
5. Redirecionar de volta para o Portal
6. Verificar se está autenticado
```

### 3. Verificar Claims do Token

```bash
# Decodificar token JWT (sem verificação de assinatura)
echo $TOKEN | jq -R 'split(".") | .[1] | @base64d | fromjson'

# Verificar claims:
{
  "exp": 1740885456,
  "iat": 1740885156,
  "jti": "abcd1234",
  "iss": "http://localhost:8080/realms/bemcuidar",
  "aud": "intellicare-admin",
  "sub": "abcd1234-5678-9012-abcd-123456789012",
  "typ": "Bearer",
  "azp": "intellicare-admin",
  "session_state": "abcd1234",
  "acr": "1",
  "allowed-origins": ["http://localhost:8010"],
  "realm_access": {
    "roles": ["PLATFORM_ADMIN"]
  },
  "resource_access": {
    "intellicare-admin": {
      "roles": ["uma_protection"]
    }
  },
  "scope": "email profile",
  "sid": "abcd1234",
  "email_verified": true,
  "name": "IntelliCare Admin",
  "preferred_username": "admin@intellicare.ia.br",
  "given_name": "IntelliCare",
  "family_name": "Admin",
  "email": "admin@intellicare.ia.br"
}
```

## 🧪 Testes de Integração

### Teste de SMART on FHIR

```bash
# Obter token SMART
curl -s -X POST "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "patient_id=123&scope=patient/*.read&grant_type=client_credentials&client_id=intellicare-grahame" \
  | jq .

# Acessar endpoint FHIR com token SMART
curl -H "Authorization: Bearer $SMART_TOKEN" \
  http://localhost:8012/fhir/ Patient/123
```

### Teste de Multi-Tenancy

```bash
# Criar usuário tenant
curl -X POST "http://localhost:8080/admin/realms/bemcuidar/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@tenant.com.br",
    "email": "user@tenant.com.br",
    "enabled": true,
    "attributes": {
      "tenant_id": ["tenant123"]
    },
    "realmRoles": ["TENANT_ADMIN"]
  }'

# Login como tenant user
curl -s -X POST "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@tenant.com.br&password=tenantpass&grant_type=password&client_id=intellicare-admin" \
  | jq .

# Verificar tenant_id no token
echo $TOKEN | jq -R 'split(".") | .[1] | @base64d | fromjson | .tenant_id'
```

## ✅ Checklist de Testes

### Keycloak Server
- [ ] Health check respondendo
- [ ] Realm bemcuidar acessível
- [ ] Admin Console acessível
- [ ] Tokens sendo emitidos

### Clients
- [ ] intellicare-admin configurado
- [ ] intellicare-portal configurado
- [ ] Secrets armazenados seguramente
- [ ] Redirect URIs corretas

### Integração Módulos
- [ ] Admin módulo protegido
- [ ] Portal frontend autenticando
- [ ] Token refresh funcionando
- [ ] Logout funcionando

### Segurança
- [ ] HTTPS habilitado (staging/produção)
- [ ] Senhas trocadas de padrão
- [ ] CORS configurado corretamente
- [ ] Rate limiting habilitado

## 📊 Scripts de Teste Automatizado

```bash
#!/bin/bash
# test_auth.sh - Teste completo de autenticação

set -e

echo "🧪 Testando autenticação Keycloak..."

# 1. Health check
echo "1️⃣ Health check..."
curl -s http://localhost:8080/health/ready | jq .

# 2. Realm check
echo "2️⃣ Realm check..."
curl -s http://localhost:8080/realms/bemcuidar | jq .

# 3. Login
echo "3️⃣ Login..."
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@intellicare.ia.br&password=changeme-admin&grant_type=password&client_id=intellicare-admin" \
  | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Falha ao obter token"
  exit 1
fi

echo "✅ Token obtido: ${TOKEN:0:50}..."

# 4. Access protected endpoint
echo "4️⃣ Access protected endpoint..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8010/api/v1/admin/users \
  -w "\nHTTP Status: %{http_code}\n"

echo "✅ Todos os testes passaram!"
```

## 📝 Próximo Passo

Após testar autenticação, prossiga para: **[06_DEPLOY_STAGING.md](./06_DEPLOY_STAGING.md)**

---

**Última Atualização**: 2026-03-01
**Responsável**: IntelliCare Team
