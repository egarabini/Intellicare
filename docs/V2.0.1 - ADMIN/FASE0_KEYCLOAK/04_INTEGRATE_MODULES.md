# 04 - Integrar Módulos com Keycloak

## 📋 Visão Geral

Este guia cobre a integração dos módulos IntelliCare com Keycloak usando `intellicare-auth`.

## 🏗️ Arquitetura de Autenticação

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Portal    │─────▶│   Keycloak   │─────▶│  Módulos    │
│  (React)    │      │  (OAuth2/OIDC)│      │  (FastAPI)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │intellicare-  │
                     │    auth      │
                     └──────────────┘
```

## 📦 Passo 1: Instalar intellicare-auth

`intellicare-auth` fornece integração Keycloak/SMART-on-FHIR para FastAPI.

### Como Funciona

1. **Configuração**: Lê `keycloak_client_secrets.json`
2. **Middleware**: Valida JWT tokens em requests
3. **Dependencies**: Fornece `get_current_user()` e `require_role()`
4. **SMART on FHIR**: Suporta padrão FHIR authentication

### Adicionar aos Módulos

```bash
# Dockerfile - já está instalado nos módulos
COPY ./intellicare-auth /tmp/intellicare-auth
RUN pip install --no-cache-dir -e /tmp/intellicare-auth || true
```

## 📝 Passo 2: Configurar Client Secrets

### Formato do Arquivo

```json
{
  "web": {
    "auth_uri": "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/auth",
    "client_id": "intellicare-admin",
    "client_secret": "admin-secret-change-in-production",
    "redirect_uris": ["http://localhost:8010/*"],
    "token_uri": "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token",
    "issuer": "http://localhost:8080/realms/bemcuidar",
    "token_introspection_uri": "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token/introspect"
  }
}
```

### Criar para Cada Módulo

```bash
# Módulo Admin
cat > intellicare-admin/keycloak_client_secrets.json << 'EOF'
{
  "web": {
    "auth_uri": "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/auth",
    "client_id": "intellicare-admin",
    "client_secret": "admin-secret-change-in-production",
    "redirect_uris": ["http://localhost:8010/*"],
    "token_uri": "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token",
    "issuer": "http://localhost:8080/realms/bemcuidar"
  }
}
EOF

# Módulo Portal
cat > intellicare-portal/keycloak_client_secrets.json << 'EOF'
{
  "web": {
    "auth_uri": "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/auth",
    "client_id": "intellicare-portal",
    "client_secret": "portal-secret-change-in-production",
    "redirect_uris": ["http://localhost:3001/*"],
    "token_uri": "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token",
    "issuer": "http://localhost:8080/realms/bemcuidar"
  }
}
EOF
```

## 🔌 Passo 3: Habilitar Auth no Módulo

### Exemplo: intellicare-admin

```python
# admin/api/app.py
from intellicare_auth.fastapi import configure_auth
from intellicare_auth.dependencies import get_current_user, require_role

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configurar Keycloak auth
    configure_auth(
        app,
        secrets_path="keycloak_client_secrets.json",
        public_routes=["/api/v1/health", "/api/v1/info", "/docs", "/openapi.json"]
    )
    yield

# Router com autenticação
@router.get("/api/v1/admin/users")
async def list_users(current_user = get_current_user()):
    """Listar todos os usuários (requer autenticação)"""
    return {"users": [...]}

# Router com role específica
@router.delete("/api/v1/admin/users/{user_id}")
async def delete_user(user_id: str, current_user = require_role("PLATFORM_ADMIN")):
    """Deletar usuário (requer role PLATFORM_ADMIN)"""
    return {"message": "User deleted"}
```

### Exemplo: Portal React

```typescript
// src/services/auth.ts
import { Configuration } from '@shared/types/auth';

const keycloakConfig: Configuration = {
  authUrl: 'http://localhost:8080/realms/bemcuidar/protocol/openid-connect/auth',
  clientId: 'intellicare-portal',
  redirectUri: 'http://localhost:3001/auth/callback',
  postLogoutRedirectUri: 'http://localhost:3001',
};

// src/pages/Login.tsx
import { useAuth } from '@contexts/AuthContext';

function LoginPage() {
  const { login } = useAuth();

  const handleLogin = () => {
    login(keycloakConfig);
  };

  return <button onClick={handleLogin}>Login com Keycloak</button>;
}
```

## 🌐 Passo 4: URLs por Ambiente

| Ambiente | Keycloak URL | Realm | Token Endpoint |
|----------|--------------|-------|----------------|
| Local | `http://localhost:8080` | bemcuidar | `http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token` |
| Staging | `https://auth.intellicare.ia.br` | bemcuidar | `https://auth.intellicare.ia.br/realms/bemcuidar/protocol/openid-connect/token` |
| Produção | `https://auth.saudeconectada.com.br` | bemcuidar | `https://auth.saudeconectada.com.br/realms/bemcuidar/protocol/openid-connect/token` |

## 🔄 Passo 5: Atualizar Variáveis de Ambiente

```bash
# .env para cada módulo
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=bemcuidar
KEYCLOAK_CLIENT_ID=intellicare-admin
KEYCLOAK_CLIENT_SECRET=admin-secret-change-in-production
```

## ✅ Checklist de Integração

Por Módulo:

- [ ] **intellicare-admin**
  - [ ] keycloak_client_secrets.json criado
  - [ ] configure_auth() no lifespan
  - [ ] Rotas protegidas com get_current_user()
  - [ ] Rotas admin protegidas com require_role()

- [ ] **intellicare-portal**
  - [ ] keycloak_client_secrets.json criado
  - [ ] AuthContext configurado
  - [ ] Login/Logout implementados
  - [ ] Token refresh configurado

- [ ] **intellicare-wanda**
  - [ ] keycloak_client_secrets.json criado
  - [ ] configure_auth() no lifespan
  - [ ] Rotas de orquestração protegidas

- [ ] **Outros módulos** (florence, oswaldo, etc)
  - [ ] Mesmo padrão dos módulos acima

## 🧪 Teste de Integração

```bash
# 1. Obter token de admin
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@intellicare.ia.br&password=changeme-admin&grant_type=password&client_id=intellicare-admin" | jq -r '.access_token')

# 2. Acessar endpoint protegido
curl -H "Authorization: Bearer $TOKEN" http://localhost:8010/api/v1/admin/users

# 3. Verificar claims
echo $TOKEN | jq .
# Deve conter: realm_access, roles, tenant_id, etc
```

## 📝 Próximo Passo

Após integrar módulos, prossiga para: **[05_TEST_AUTH.md](./05_TEST_AUTH.md)**

---

**Última Atualização**: 2026-03-01
**Responsável**: IntelliCare Team
