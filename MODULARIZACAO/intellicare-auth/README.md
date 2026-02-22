# 🔐 IntelliCare Auth - Biblioteca de Autenticação Keycloak

Biblioteca compartilhada para integração com Keycloak GSI em todos os módulos IntelliCare.

## 🎯 Objetivo

Fornecer autenticação e autorização centralizada via **Keycloak** (`keycloak.gsi.srv.br`) para os 9 módulos IntelliCare, implementando:

- ✅ **SSO (Single Sign-On)**: Login único em todos os módulos
- ✅ **RBAC (Role-Based Access Control)**: Controle de acesso baseado em roles
- ✅ **Validação de Tokens JWT**: Validação local com cache JWKS
- ✅ **Middleware FastAPI**: Integração transparente
- ✅ **Decorators**: Proteção de endpoints por roles

---

## 🚀 Instalação

```bash
# Desenvolvimento (editable mode)
pip install -e .

# Produção
pip install intellicare-auth
```

---

## 📋 Configuração

### Variáveis de Ambiente

```bash
# Keycloak Server
KEYCLOAK_SERVER_URL=https://keycloak.gsi.srv.br/auth
KEYCLOAK_REALM=saudeplanner.com.br

# Client Credentials (específico por módulo)
KEYCLOAK_CLIENT_ID=intellicare-core
KEYCLOAK_CLIENT_SECRET=your-client-secret-here
```

---

## 🔧 Uso Básico

### 1. Proteger Endpoints com Middleware

```python
from fastapi import FastAPI, Depends
from intellicare_auth import get_current_user, requires_role

app = FastAPI()

# Endpoint público
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint protegido (requer autenticação)
@app.get("/api/data")
async def get_data(user: dict = Depends(get_current_user)):
    return {
        "data": "sensitive",
        "user": user["preferred_username"]
    }

# Endpoint com role específica
@app.get("/api/admin")
@requires_role("intellicare_admin")
async def admin_only(user: dict = Depends(get_current_user)):
    return {"message": "Admin access granted"}
```

### 2. Obter Token (Client Credentials)

```python
from intellicare_auth import KeycloakClient

client = KeycloakClient(
    server_url="https://keycloak.gsi.srv.br/auth",
    realm="saudeplanner.com.br",
    client_id="intellicare-core",
    client_secret="your-secret"
)

# Obter token
token = await client.get_client_token()
print(token["access_token"])
```

### 3. Validar Token

```python
# Validação automática via middleware
user_info = await client.validate_token(access_token)
print(user_info["preferred_username"])
print(user_info["realm_access"]["roles"])
```

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────┐
│   Keycloak GSI (keycloak.gsi.srv.br)       │
│   Realm: saudeplanner.com.br                │
│   - 9 Clients (1 por módulo)                │
│   - Roles: intellicare_admin, doctor, etc.  │
└──────────────┬──────────────────────────────┘
               │ OAuth2/OIDC
               │
┌──────────────▼──────────────────────────────┐
│   intellicare-auth (esta biblioteca)        │
│   - KeycloakClient                          │
│   - Middleware FastAPI                      │
│   - Decorators                              │
│   - Cache JWKS                              │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Core    │ │ Wanda   │ │ Donabe- │
│         │ │         │ │ dian    │
└─────────┘ └─────────┘ └─────────┘
```

---

## 📚 Documentação Completa

Ver: `docs/` para guias detalhados

---

## 🧪 Testes

```bash
# Rodar testes
pytest

# Com cobertura
pytest --cov=intellicare_auth --cov-report=html
```

---

## 📦 Estrutura

```
intellicare-auth/
├── intellicare_auth/
│   ├── __init__.py
│   ├── client.py          # KeycloakClient
│   ├── middleware.py      # FastAPI middleware
│   ├── decorators.py      # @requires_role
│   ├── config.py          # Configurações
│   └── exceptions.py      # Exceções customizadas
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

---

**Versão**: 1.0.0  
**Autor**: IntelliCare Team  
**Licença**: MIT

