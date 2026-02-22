# 🎯 INTEGRAÇÃO: intellicare-donabedian (Módulo Piloto)

Guia detalhado para integrar autenticação Keycloak no módulo **intellicare-donabedian**.

---

## 📊 CONTEXTO

**Módulo**: intellicare-donabedian  
**Função**: Avaliação de qualidade baseada em Donabedian  
**Status Atual**: 86 arquivos, ~11.000 linhas, 196 testes  
**Porta**: 8003  
**Tempo Estimado**: 4-6 horas

---

## 🎯 OBJETIVOS

- ✅ Proteger endpoints de API com autenticação JWT
- ✅ Implementar controle de acesso por roles
- ✅ Manter compatibilidade com testes existentes
- ✅ Documentar mudanças

---

## 📋 PRÉ-REQUISITOS

- [ ] Keycloak configurado (executar `scripts/setup_keycloak.py`)
- [ ] Client `intellicare-donabedian` criado
- [ ] Client secret obtido
- [ ] Usuários de teste criados

---

## 🔧 PASSO 1: Instalar Biblioteca (5 min)

```bash
cd MODULARIZACAO/intellicare-donabedian

# Instalar intellicare-auth
pip install -e ../intellicare-auth

# Verificar instalação
python -c "from intellicare_auth import get_current_user; print('✅ OK')"
```

---

## ⚙️ PASSO 2: Configurar Environment (5 min)

### 2.1 Criar arquivo `.env`

```bash
cat > .env << 'EOF'
# Keycloak Configuration
KEYCLOAK_SERVER_URL=https://keycloak.gsi.srv.br/auth
KEYCLOAK_REALM=saudeplanner.com.br
KEYCLOAK_CLIENT_ID=intellicare-donabedian
KEYCLOAK_CLIENT_SECRET=<COPIAR_DO_keycloak_client_secrets.json>

# Configurações opcionais
KEYCLOAK_JWKS_CACHE_TTL=300
KEYCLOAK_TOKEN_CACHE_TTL=60
KEYCLOAK_VERIFY_SSL=true
EOF
```

### 2.2 Obter Client Secret

```bash
# Abrir arquivo de secrets
cat ../intellicare-auth/keycloak_client_secrets.json | grep intellicare-donabedian -A 1

# Copiar secret e colar no .env
```

---

## 📝 PASSO 3: Modificar main.py (30 min)

### 3.1 Localizar arquivo

```bash
# Arquivo principal da API
src/donabedian/api/main.py
```

### 3.2 Adicionar imports

```python
# No topo do arquivo, adicionar:
from intellicare_auth import get_current_user, get_optional_user, requires_role
```

### 3.3 Exemplo de modificação

**ANTES**:
```python
from fastapi import FastAPI

app = FastAPI(title="IntelliCare Donabedian")

@app.get("/api/v1/pillars")
async def list_pillars():
    return {"pillars": [...]}
```

**DEPOIS**:
```python
from fastapi import FastAPI, Depends
from intellicare_auth import get_current_user, requires_role

app = FastAPI(title="IntelliCare Donabedian")

# Endpoint público (sem mudanças)
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint protegido (requer autenticação)
@app.get("/api/v1/pillars")
async def list_pillars(user: dict = Depends(get_current_user)):
    return {
        "pillars": [...],
        "user": user["preferred_username"]
    }

# Endpoint com role (apenas admin pode criar)
@app.post("/api/v1/pillars")
@requires_role("intellicare_admin")
async def create_pillar(user: dict = Depends(get_current_user)):
    return {"message": "Pillar created"}
```

---

## 🛡️ PASSO 4: Proteger Endpoints por Categoria (2 horas)

### 4.1 Endpoints Públicos (sem autenticação)

```python
# Manter sem mudanças:
- /health
- /info
- /docs
- /openapi.json
```

### 4.2 Endpoints de Leitura (autenticação obrigatória)

```python
# Adicionar: user: dict = Depends(get_current_user)

@app.get("/api/v1/pillars")
@app.get("/api/v1/pillars/{pillar_id}")
@app.get("/api/v1/indicators")
@app.get("/api/v1/indicators/{indicator_id}")
@app.get("/api/v1/measurements")
```

### 4.3 Endpoints de Escrita (role: admin ou profissional)

```python
# Adicionar: @requires_any_role(["intellicare_admin", "intellicare_doctor", "intellicare_nurse"])

@app.post("/api/v1/pillars")
@app.put("/api/v1/pillars/{pillar_id}")
@app.delete("/api/v1/pillars/{pillar_id}")
@app.post("/api/v1/indicators")
@app.post("/api/v1/measurements")
```

### 4.4 Endpoints Administrativos (role: admin)

```python
# Adicionar: @requires_role("intellicare_admin")

@app.delete("/api/v1/indicators/{indicator_id}")
@app.post("/api/v1/admin/reset")
```

---

## 🧪 PASSO 5: Testar (1 hora)

### 5.1 Iniciar servidor

```bash
cd MODULARIZACAO/intellicare-donabedian
uvicorn src.donabedian.api.main:app --reload --port 8003
```

### 5.2 Testar endpoint público

```bash
curl http://localhost:8003/health
# Esperado: {"status": "healthy"}
```

### 5.3 Testar endpoint protegido (sem token)

```bash
curl http://localhost:8003/api/v1/pillars
# Esperado: 401 Unauthorized
```

### 5.4 Obter token

```bash
# Via client credentials
curl -X POST https://keycloak.gsi.srv.br/auth/realms/saudeplanner.com.br/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=intellicare-donabedian" \
  -d "client_secret=SEU_SECRET_AQUI" \
  | jq -r '.access_token' > token.txt

# Salvar em variável
export TOKEN=$(cat token.txt)
```

### 5.5 Testar com token

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8003/api/v1/pillars
# Esperado: {"pillars": [...], "user": "..."}
```

---

## ✅ PASSO 6: Atualizar Testes (1-2 horas)

### 6.1 Criar fixture de autenticação

```python
# tests/conftest.py

import pytest
from intellicare_auth import KeycloakClient, KeycloakConfig

@pytest.fixture
async def auth_token():
    """Fixture para obter token de teste."""
    config = KeycloakConfig(
        client_id="intellicare-donabedian",
        client_secret="SEU_SECRET"
    )
    client = KeycloakClient(config)
    token_data = await client.get_client_token()
    return token_data["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    """Headers com autenticação."""
    return {"Authorization": f"Bearer {auth_token}"}
```

### 6.2 Atualizar testes existentes

```python
# ANTES
def test_list_pillars(client):
    response = client.get("/api/v1/pillars")
    assert response.status_code == 200

# DEPOIS
def test_list_pillars(client, auth_headers):
    response = client.get("/api/v1/pillars", headers=auth_headers)
    assert response.status_code == 200
```

---

## 📚 PASSO 7: Documentar (30 min)

### 7.1 Atualizar README.md

Adicionar seção de autenticação:

```markdown
## 🔐 Autenticação

Este módulo usa Keycloak para autenticação.

### Configuração

Ver `.env.example` para variáveis necessárias.

### Obter Token

\`\`\`bash
curl -X POST https://keycloak.gsi.srv.br/auth/realms/saudeplanner.com.br/protocol/openid-connect/token \\
  -d "grant_type=client_credentials" \\
  -d "client_id=intellicare-donabedian" \\
  -d "client_secret=SEU_SECRET"
\`\`\`
```

---

## ✅ CHECKLIST FINAL

- [ ] Biblioteca instalada
- [ ] `.env` configurado
- [ ] Imports adicionados em `main.py`
- [ ] Endpoints públicos identificados
- [ ] Endpoints protegidos com `get_current_user`
- [ ] Endpoints com roles configurados
- [ ] Servidor iniciado e testado
- [ ] Token obtido com sucesso
- [ ] Endpoints testados com token
- [ ] Testes atualizados
- [ ] README atualizado
- [ ] Commit realizado

---

## 🎉 RESULTADO ESPERADO

- ✅ Todos os endpoints protegidos
- ✅ Controle de acesso por roles funcionando
- ✅ Testes passando
- ✅ Documentação atualizada
- ✅ Pronto para produção

---

**Tempo total**: 4-6 horas  
**Próximo módulo**: intellicare-wanda (orquestrador)

