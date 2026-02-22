# 🚀 PLANO PRÁTICO - INTEGRAÇÃO KEYCLOAK PARA DEV1

## 📋 TAREFAS IMEDIATAS (HOJE/AMANHÃ)

### 1. OBTER ACESSO AO KEYCLOAK GSI
**Ação:** Solicitar ao time do GSI:
- Acesso admin ao Keycloak: `https://keycloak.gsi.srv.br/auth/admin/`
- Credenciais de administrador
- Informações sobre realm a usar

**Perguntas para o GSI:**
1. Qual realm devemos usar para o INTELLICARE?
2. Podemos criar 9 novos clients (1 por módulo)?
3. Como estão os usuários configurados (vêm do AD/LDAP)?
4. Quais permissões temos?

### 2. EXPLORAR KEYCLOAK EXISTENTE
```bash
# Testar conectividade
curl -s https://keycloak.gsi.srv.br/auth/realms/gsisaude/.well-known/openid-configuration | jq .

# Verificar endpoints importantes:
# - /.well-known/openid-configuration
# - /protocol/openid-connect/certs (JWKS)
# - /protocol/openid-connect/token
# - /protocol/openid-connect/userinfo
```

### 3. CRIAR CLIENTS NO KEYCLOAK
**Para cada módulo (9 total):**
1. Acessar `https://keycloak.gsi.srv.br/auth/admin/`
2. Clients → Create
3. Configurar:
   - **Client ID**: `intellicare-wanda` (exemplo)
   - **Name**: IntelliCare Wanda Module
   - **Client Protocol**: openid-connect
   - **Access Type**: confidential
   - **Valid Redirect URIs**: `http://localhost:8001/*` (ajustar porta)
   - **Service Accounts Enabled**: ON
4. Salvar e anotar o **Client Secret**

**Módulos a configurar:**
- `intellicare-core`
- `intellicare-wanda`
- `intellicare-florence`
- `intellicare-oswaldo`
- `intellicare-zilda`
- `intellicare-geralda`
- `intellicare-donabedian`
- `intellicare-portal`
- `intellicare-comunicacao`

### 4. CRIAR ROLES
**Estrutura sugerida no Keycloak:**
1. Realm Roles → Create Role
2. Criar hierarquia:
   - `intellicare_admin`
   - `intellicare_doctor`
   - `intellicare_nurse`
   - `intellicare_care_coordinator`
   - `intellicare_patient`

### 5. CONFIGURAR ATRIBUTOS (Mappers)
Para cada client, em Mappers → Create:
1. **hospital_id**: User Attribute → Token Claim
2. **specialty**: User Attribute → Token Claim
3. **license_number**: User Attribute → Token Claim
4. **department**: User Attribute → Token Claim

---

## 🔧 SEMANA 1: BIBLIOTECA DE INTEGRAÇÃO

### Criar Projeto `intellicare-auth`
```bash
# Na raiz do projeto INTELLICARE
mkdir intellicare-auth
cd intellicare-auth

# Ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Estrutura inicial
touch requirements.txt pyproject.toml setup.py
mkdir intellicare_auth
touch intellicare_auth/__init__.py
touch intellicare_auth/client.py
touch intellicare_auth/middleware.py
touch intellicare_auth/decorators.py
```

### `requirements.txt`
```txt
fastapi>=0.104.0
python-keycloak>=2.10.0
pyjwt>=2.8.0
httpx>=0.25.0
cachetools>=5.3.0
pydantic>=2.0.0
```

### Código Essencial - `client.py`
```python
import httpx
from cachetools import TTLCache
import jwt
import json

class GSIKeycloakClient:
    def __init__(self, realm="gsisaude"):
        self.server_url = "https://keycloak.gsi.srv.br/auth"
        self.realm = realm
        self.jwks_cache = TTLCache(maxsize=1, ttl=300)
    
    async def get_jwks(self):
        """Busca JWKS do Keycloak"""
        cached = self.jwks_cache.get("jwks")
        if cached:
            return cached
        
        async with httpx.AsyncClient() as client:
            url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/certs"
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            jwks = response.json()
            self.jwks_cache["jwks"] = jwks
            return jwks
    
    async def validate_token(self, token: str):
        """Valida token JWT localmente com JWKS"""
        jwks = await self.get_jwks()
        # Implementar validação JWT
        # Retornar payload decodificado
```

### `middleware.py`
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .client import GSIKeycloakClient

security = HTTPBearer()
keycloak_client = GSIKeycloakClient()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        user_info = await keycloak_client.validate_token(token)
        return user_info
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
```

### `decorators.py`
```python
from functools import wraps
from fastapi import Depends
from .middleware import get_current_user

def requires_role(role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = await get_current_user()
            if role not in user.get("realm_access", {}).get("roles", []):
                raise HTTPException(status_code=403, detail=f"Role '{role}' requerida")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 🎯 SEMANA 2: INTEGRAR PRIMEIROS MÓDULOS

### 1. Módulo Piloto: `intellicare-core`
```bash
cd MODULARIZACAO/intellicare-core

# Instalar biblioteca localmente
pip install -e ../intellicare-auth

# Adicionar ao pyproject.toml do módulo:
# dependencies = ["intellicare-auth"]
```

### 2. Modificar API do Core
```python
# No main.py do módulo core
from fastapi import FastAPI, Depends
from intellicare_auth import get_current_user, requires_role

app = FastAPI()

# Endpoint público
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint protegido
@app.get("/api/config")
@requires_role("intellicare_admin")
async def get_config(user: dict = Depends(get_current_user)):
    return {
        "config": "sensitive_data",
        "user": user.get("preferred_username"),
        "hospital": user.get("hospital_id")
    }

# Endpoint para verificar conexão Keycloak
@app.get("/auth/status")
async def auth_status():
    from intellicare_auth.client import GSIKeycloakClient
    client = GSIKeycloakClient()
    try:
        jwks = await client.get_jwks()
        return {"status": "connected", "keys": len(jwks.get("keys", []))}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### 3. Testar
```bash
# Iniciar módulo
uvicorn src.intellicare_core.api.main:app --reload --port 8000

# Testar endpoints
curl http://localhost:8000/health
# Esperado: {"status": "healthy"}

curl http://localhost:8000/auth/status
# Esperado: {"status": "connected", "keys": N}

curl http://localhost:8000/api/config
# Esperado: 401 Unauthorized (sem token)
```

### 4. Obter Token de Teste
```bash
# Usar client do módulo core para obter token
curl -X POST https://keycloak.gsi.srv.br/auth/realms/gsisaude/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=intellicare-core" \
  -d "client_secret=SEU_CLIENT_SECRET_AQUI"

# Resposta terá access_token
# Usar para testar endpoint protegido:
curl -H "Authorization: Bearer SEU_TOKEN_AQUI" http://localhost:8000/api/config
```

---

## 📈 SEMANA 3: EXPANDIR PARA OUTROS MÓDULOS

### Ordem Sugerida:
1. `intellicare-wanda` (orquestrador crítico)
2. `intellicare-portal` (frontend React)
3. `intellicare-florence` (análise clínica)
4. `intellicare-oswaldo` (doenças crônicas)
5. Demais módulos

### Padrão para Cada Módulo:
1. Instalar `intellicare-auth`
2. Importar `get_current_user` e `requires_role`
3. Proteger endpoints com decorators
4. Testar com token

### Portal React (módulo `intellicare-portal`)
```javascript
// Instalar keycloak-js
npm install keycloak-js

// Configuração
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'https://keycloak.gsi.srv.br/auth',
  realm: 'gsisaude',
  clientId: 'intellicare-portal'
});

// Inicializar
keycloak.init({ onLoad: 'login-required' })
  .then(authenticated => {
    if (authenticated) {
      console.log('Usuário autenticado');
      // Salvar token para usar nas APIs
      localStorage.setItem('kc_token', keycloak.token);
    }
  });
```

---

## 🧪 TESTES

### Testes Unitários para Biblioteca
```python
# tests/test_client.py
import pytest
from unittest.mock import Mock, patch
from intellicare_auth.client import GSIKeycloakClient

@pytest.mark.asyncio
async def test_get_jwks():
    client = GSIKeycloakClient()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"keys": [{"kid": "test"}]}
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        jwks = await client.get_jwks()
        assert "keys" in jwks
        assert len(jwks["keys"]) == 1
```

### Testes de Integração
```python
# tests/test_api_auth.py
from fastapi.testclient import TestClient
from src.intellicare_core.api.main import app

client = TestClient(app)

def test_protected_endpoint_without_token():
    response = client.get("/api/config")
    assert response.status_code == 401

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## 📊 MONITORAMENTO

### Métricas Importantes:
1. **Conectividade Keycloak**: `auth/status` endpoint
2. **Latência autenticação**: tempo para validar token
3. **Taxa de erro**: autenticações falhas vs sucesso
4. **Uso de roles**: quais roles mais utilizadas

### Dashboard Simples:
```python
@app.get("/auth/metrics")
@requires_role("intellicare_admin")
async def get_auth_metrics():
    return {
        "keycloak_status": "connected",
        "token_validations_today": 150,
        "failed_authentications": 3,
        "avg_validation_time_ms": 45.2
    }
```

---

## 🚨 TROUBLESHOOTING

### Problemas Comuns:

1. **"Connection refused" ao Keycloak**
   - Verificar VPN/redes
   - Testar com `curl` primeiro
   - Verificar firewall

2. **Token inválido ou expirado**
   - Verificar expiration time no token
   - Verificar audience (deve ser o client_id correto)
   - Verificar issuer (deve ser do Keycloak GSI)

3. **Role não encontrada**
   - Verificar se role existe no Keycloak
   - Verificar se está mapeada para o token
   - Verificar composite roles

4. **Client secret incorreto**
   - Gerar novo secret no Keycloak
   - Atualizar no código/ambiente

---

## ✅ CHECKLIST DE PROGRESSO

### Fase 1 - Configuração:
- [ ] Acesso ao Keycloak GSI obtido
- [ ] 9 clients criados
- [ ] Client secrets salvos
- [ ] Roles configuradas
- [ ] Mappers de atributos configurados

### Fase 2 - Biblioteca:
- [ ] Projeto `intellicare-auth` criado
- [ ] Cliente GSI implementado
- [ ] Middleware FastAPI funcionando
- [ ] Decorators para roles
- [ ] Testes unitários

### Fase 3 - Integração:
- [ ] Módulo `intellicare-core` integrado
- [ ] Módulo `intellicare-wanda` integrado
- [ ] Módulo `intellicare-portal` (React) integrado
- [ ] Demais módulos integrados
- [ ] Testes de integração

### Fase 4 - Produção:
- [ ] Monitoramento configurado
- [ ] Documentação completa
- [ ] Treinamento para equipe
- [ ] Deploy em staging

---

## 📞 SUPORTE

### Contatos:
- **GSI**: Suporte Keycloak e acesso
- **Equipe INTELLICARE**: Dúvidas de integração
- **DEV1 Backup**: [definir contato]

### Canais:
- Slack/Teams: `#keycloak-integration`
- Email: [lista de discussão]
- Reuniões: Daily standup para progresso

---

**🎯 PRÓXIMOS PASSOS PARA DEV1:**
1. **Hoje**: Solicitar acesso ao Keycloak GSI
2. **Amanhã**: Explorar console e criar clients
3. **Dia 3**: Começar biblioteca `intellicare-auth`
4. **Dia 4**: Integrar primeiro módulo (`intellicare-core`)
5. **Dia 5**: Testar e documentar

**🚀 BOA SORTE!**