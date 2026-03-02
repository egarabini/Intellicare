# 🔐 IntelliCare Auth - Autenticação Keycloak + Servidor SSO

Biblioteca compartilhada para integração com Keycloak em todos os módulos IntelliCare + infraestrutura do servidor Keycloak.

## 🎯 Objetivo

Fornecer autenticação e autorização centralizada via **Keycloak** para os módulos IntelliCare, implementando:

- ✅ **SSO (Single Sign-On)**: Login único em todos os módulos
- ✅ **RBAC (Role-Based Access Control)**: Controle de acesso baseado em roles
- ✅ **Validação de Tokens JWT**: Validação local com cache JWKS
- ✅ **Middleware FastAPI**: Integração transparente
- ✅ **Decorators**: Proteção de endpoints por roles
- ✅ **Servidor Keycloak**: Infraestrutura completa com Docker Compose

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────┐
│   Keycloak Server (Docker)                  │
│   URL: auth.intellicare.ia.br               │
│   Realm: bemcuidar                          │
│   - Clients por módulo                      │
│   - Roles: PLATFORM_ADMIN, TENANT_ADMIN, etc│
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
│ Florence│ │ Wanda   │ │ Donabe- │
│         │ │         │ │ dian    │
└─────────┘ └─────────┘ └─────────┘
```

---

## 📦 Estrutura

```
intellicare-auth/
├── keycloak/                      # Servidor Keycloak (Infraestrutura)
│   ├── import/
│   │   └── bemcuidar-realm.json   # Configuração do realm
│   ├── certs/                     # Certificados SSL
│   └── themes/                    # Temas customizados (opcional)
├── intellicare_auth/              # Biblioteca Python
│   ├── __init__.py
│   ├── client.py                  # KeycloakClient
│   ├── middleware.py              # FastAPI middleware
│   ├── decorators.py              # @requires_role
│   ├── config.py                  # Configurações
│   └── exceptions.py              # Exceções customizadas
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

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
KEYCLOAK_SERVER_URL=https://auth.intellicare.ia.br
KEYCLOAK_REALM=bemcuidar

# Client Credentials (específico por módulo)
KEYCLOAK_CLIENT_ID=intellicare-admin
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
@requires_role("PLATFORM_ADMIN")
async def admin_only(user: dict = Depends(get_current_user)):
    return {"message": "Admin access granted"}
```

### 2. Obter Token (Client Credentials)

```python
from intellicare_auth import KeycloakClient

client = KeycloakClient(
    server_url="https://auth.intellicare.ia.br",
    realm="bemcuidar",
    client_id="intellicare-admin",
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

## 🐳 Servidor Keycloak (Docker)

### Iniciar Servidor

```bash
# No diretório raiz do projeto (não aqui em intellicare-auth/)
docker-compose -f docker-compose.keycloak.yml up -d

# Verificar saúde
curl http://localhost:8080/health/ready

# Admin Console
# URL: http://localhost:8080/admin
# User: admin
# Password: (ver .env.keycloak na raiz do projeto)
```

### Configuração do Servidor

O servidor Keycloak é configurado via `docker-compose.keycloak.yml` (na raiz do projeto):

- **Imagem**: quay.io/keycloak/keycloak:24.0
- **Banco de Dados**: PostgreSQL 15 dedicado
- **Realm Import**: `intellicare-auth/keycloak/import/bemcuidar-realm.json`
- **Portas**: 8080 (HTTP), 8443 (HTTPS)
- **Traefik**: Configurado para `auth.intellicare.ia.br`

---

## 🌐 URLs de Acesso

| Ambiente | Keycloak URL | Admin Console |
|----------|--------------|---------------|
| Local | `http://localhost:8080` | `http://localhost:8080/admin` |
| Staging | `https://auth.intellicare.ia.br` | `https://auth.intellicare.ia.br/admin` |
| Produção | `https://auth.saudeconectada.com.br` | `https://auth.saudeconectada.com.br/admin` |

---

## 📚 Documentação Completa

Ver: `../../docs/V2.0.1 - ADMIN/FASE0_KEYCLOAK/` para guias detalhados de setup e deploy.

---

## 🧪 Testes

```bash
# Rodar testes
pytest

# Com cobertura
pytest --cov=intellicare_auth --cov-report=html
```

---

**Versão**: 2.0.0
**Autor**: IntelliCare Team
**Licença**: MIT

