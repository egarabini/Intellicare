# 🚀 Guia de Integração - IntelliCare Auth

Guia passo a passo para integrar `intellicare-auth` em um módulo IntelliCare.

---

## 📋 Pré-requisitos

1. **Keycloak configurado** em `keycloak.gsi.srv.br`
2. **Client criado** no Keycloak para seu módulo
3. **Client Secret** obtido
4. **Roles configuradas** no realm

---

## 🔧 PASSO 1: Instalar Biblioteca

```bash
cd MODULARIZACAO/seu-modulo

# Desenvolvimento (editable)
pip install -e ../intellicare-auth

# Ou adicionar ao pyproject.toml
```

**pyproject.toml:**
```toml
[project]
dependencies = [
    "intellicare-auth>=1.0.0",
    # ... outras dependências
]
```

---

## ⚙️ PASSO 2: Configurar Variáveis de Ambiente

Criar arquivo `.env` na raiz do módulo:

```bash
# Keycloak Configuration
KEYCLOAK_SERVER_URL=https://keycloak.gsi.srv.br/auth
KEYCLOAK_REALM=saudeplanner.com.br
KEYCLOAK_CLIENT_ID=intellicare-donabedian  # Seu client ID
KEYCLOAK_CLIENT_SECRET=h6AmFgY4S9MwJFMEXXBQf6Wy7Ts1TkP  # Seu secret

# Opcional: Configurações avançadas
KEYCLOAK_JWKS_CACHE_TTL=300
KEYCLOAK_TOKEN_CACHE_TTL=60
KEYCLOAK_VERIFY_SSL=true
```

---

## 📝 PASSO 3: Modificar main.py

### Antes (sem autenticação):

```python
from fastapi import FastAPI

app = FastAPI(title="IntelliCare Donabedian")

@app.get("/api/v1/pillars")
async def list_pillars():
    return {"pillars": [...]}
```

### Depois (com autenticação):

```python
from fastapi import FastAPI, Depends
from intellicare_auth import get_current_user, requires_role

app = FastAPI(title="IntelliCare Donabedian")

# Endpoint público (sem mudanças)
@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}

# Endpoint protegido (requer autenticação)
@app.get("/api/v1/pillars")
async def list_pillars(user: dict = Depends(get_current_user)):
    return {
        "pillars": [...],
        "user": user["preferred_username"]
    }

# Endpoint com role específica
@app.post("/api/v1/pillars")
@requires_role("intellicare_admin")
async def create_pillar(user: dict = Depends(get_current_user)):
    return {"message": "Pillar created"}
```

---

## 🧪 PASSO 4: Testar

### 4.1 Iniciar Módulo

```bash
uvicorn src.donabedian.api.main:app --reload --port 8003
```

### 4.2 Testar Endpoint Público

```bash
curl http://localhost:8003/api/v1/health
# Esperado: {"status": "healthy"}
```

### 4.3 Testar Endpoint Protegido (sem token)

```bash
curl http://localhost:8003/api/v1/pillars
# Esperado: 401 Unauthorized
```

### 4.4 Obter Token

```bash
# Via client credentials
curl -X POST https://keycloak.gsi.srv.br/auth/realms/saudeplanner.com.br/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=intellicare-donabedian" \
  -d "client_secret=h6AmFgY4S9MwJFMEXXBQf6Wy7Ts1TkP"

# Resposta:
# {
#   "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "Bearer",
#   "expires_in": 300
# }
```

### 4.5 Testar com Token

```bash
export TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -H "Authorization: Bearer $TOKEN" http://localhost:8003/api/v1/pillars
# Esperado: {"pillars": [...], "user": "..."}
```

---

## 🎯 PASSO 5: Proteger Endpoints Existentes

### Estratégia Recomendada:

1. **Endpoints públicos**: `/health`, `/info` → Sem mudanças
2. **Endpoints de leitura**: GET → `Depends(get_current_user)`
3. **Endpoints de escrita**: POST/PUT/DELETE → `@requires_role("admin")`

### Exemplo Completo:

```python
from fastapi import APIRouter, Depends
from intellicare_auth import get_current_user, requires_role, requires_any_role

router = APIRouter()

# Público
@router.get("/health")
async def health():
    return {"status": "healthy"}

# Autenticado (qualquer usuário)
@router.get("/pillars")
async def list_pillars(user: dict = Depends(get_current_user)):
    return {"pillars": [...]}

# Apenas admin
@router.post("/pillars")
@requires_role("intellicare_admin")
async def create_pillar(user: dict = Depends(get_current_user)):
    return {"message": "Created"}

# Profissionais de saúde
@router.post("/measurements")
@requires_any_role(["doctor", "nurse", "nutritionist"])
async def create_measurement(user: dict = Depends(get_current_user)):
    return {"message": "Measurement created"}
```

---

## ✅ Checklist de Integração

- [ ] Biblioteca instalada
- [ ] Variáveis de ambiente configuradas
- [ ] `get_current_user` importado
- [ ] Endpoints protegidos com `Depends(get_current_user)`
- [ ] Roles aplicadas com `@requires_role()`
- [ ] Testes com token funcionando
- [ ] Documentação atualizada

---

## 🐛 Troubleshooting

Ver: `TROUBLESHOOTING.md`

---

**Próximo**: Integrar frontend React com `keycloak-js`

