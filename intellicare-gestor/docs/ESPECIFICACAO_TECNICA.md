# ESPECIFICAÇÃO TÉCNICA — intellicare-gestor

**Módulo:** intellicare-gestor
**Versão:** 1.0
**Data:** 2026-03-08
**Status:** Aprovada para implementação

---

## 1. Correções obrigatórias (antes de qualquer feature nova)

### 1.1 pyproject.toml — declarar intellicare-auth explicitamente

```toml
[tool.poetry.dependencies]
intellicare-core = {path = "../intellicare-core", develop = true}
intellicare-auth = {path = "../intellicare-auth", develop = true}  # ADICIONAR
```

Remover o try/except do app.py — o módulo DEVE ter a lib disponível:
```python
# REMOVER:
# try:
#     from intellicare_auth.fastapi import configure_auth
#     _HAS_AUTH = True
# except ImportError:
#     _HAS_AUTH = False

# USAR diretamente:
from intellicare_auth.fastapi import configure_auth
```

### 1.2 app.py — configure_auth incondicional

```python
# ANTES:
if _HAS_AUTH:
    configure_auth(app, secrets_path="keycloak_client_secrets.json")

# DEPOIS:
configure_auth(app, secrets_path="keycloak_client_secrets.json")
```

### 1.3 deps.py — adicionar require_tenant_gestor

```python
from intellicare_auth.fastapi.deps import require_role
from intellicare_core.tenant import TenantContext

async def require_tenant_gestor(
    request: Request,
    payload: dict = Depends(require_role("TENANT_GESTOR"))
) -> dict:
    """
    Valida que o usuário tem role TENANT_GESTOR E
    injeta o tenant_id do token no request.state.
    """
    tenant_id = payload.get("tenant_id") or payload.get("azp")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="tenant_id ausente no token")
    request.state.tenant_id = tenant_id
    return payload
```

### 1.4 Adicionar auth guards em TODAS as rotas

Em todos os arquivos de rota (`user_routes.py`, `role_routes.py`, etc.):

```python
# ANTES:
@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    ...

# DEPOIS:
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_ctx),
    _: dict = Depends(require_tenant_gestor)   # ADICIONAR EM TODAS
):
    ...
```

### 1.5 Isolamento de tenant em todas as queries

TODAS as queries devem filtrar pelo `tenant_id`:

```python
# ERRADO — retorna dados de todos os tenants:
result = await db.execute(select(User))

# CORRETO — filtra pelo tenant do token:
result = await db.execute(
    select(User).where(User.tenant_id == ctx.tenant_id)
)
```

---

## 2. Configuração Keycloak

### Cliente `intellicare-gestor`

```
Client ID: intellicare-gestor
Client Type: confidential (OpenID Connect)
Valid Redirect URIs: https://gestor.intellicare.ia.br/*
Web Origins: https://gestor.intellicare.ia.br
Service Account Roles: true
```

### Token customizado — claim tenant_id

O Keycloak deve adicionar o `tenant_id` no token do gestor.
Configurar via **Protocol Mapper** no cliente `intellicare-gestor`:

```
Mapper Type: User Attribute
Token Claim Name: tenant_id
User Attribute: tenant_id
Claim JSON Type: String
Add to ID token: ON
Add to access token: ON
```

O `tenant_id` é definido no atributo do usuário no Keycloak quando o
`intellicare-admin` cria o usuário gestor.

### keycloak_client_secrets.json

```json
{
  "realm": "intellicare",
  "auth-server-url": "https://auth.intellicare.ia.br",
  "resource": "intellicare-gestor",
  "credentials": {
    "secret": "<gerado no Keycloak>"
  }
}
```

---

## 3. Banco de dados

### Schema por tenant

```
PostgreSQL database: intellicare_db
Schema: {tenant_slug}_gestor    (ex: clinica_norte_gestor)
```

O `TenantAwareSessionFactory` (já em uso no gestor) gerencia a troca de schema
automaticamente com base no `tenant_id` da requisição.

### Tabelas principais

```sql
-- units (unidades)
CREATE TABLE units (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL,
    name        VARCHAR(255) NOT NULL,
    type        VARCHAR(50),       -- clinica, hospital, ubs, telemedicina
    cnes        VARCHAR(7),        -- código CNES do estabelecimento
    address     TEXT,
    active      BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- professionals
CREATE TABLE professionals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    name            VARCHAR(255) NOT NULL,
    cpf             VARCHAR(11),
    council_type    VARCHAR(20),   -- CRM, COREN, CRO, etc.
    council_number  VARCHAR(20),
    specialty       VARCHAR(100),
    active          BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- allocations (alocação profissional ↔ unidade)
CREATE TABLE allocations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    professional_id UUID REFERENCES professionals(id),
    unit_id         UUID REFERENCES units(id),
    role_in_unit    VARCHAR(100),  -- ex: "Plantonista", "Chefe de Serviço"
    workload_hours  INTEGER,       -- carga horária semanal
    start_date      DATE NOT NULL,
    end_date        DATE,
    active          BOOLEAN DEFAULT true
);

-- users (acesso ao portal)
CREATE TABLE gestor_users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    professional_id UUID REFERENCES professionals(id),
    keycloak_id     VARCHAR(255) UNIQUE,  -- ID do usuário no Keycloak
    email           VARCHAR(255) UNIQUE NOT NULL,
    role_id         UUID REFERENCES roles(id),
    active          BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. Variáveis de ambiente

No `docker-compose.full.yml`:

```yaml
gestor:
  environment:
    - INTELLICARE_GESTOR_DATABASE_URL=${INTELLICARE_GESTOR_DATABASE_URL}
    - GESTOR_DATABASE_SCHEMA=${GESTOR_DATABASE_SCHEMA:-intellicare_gestor}
    - INTELLICARE_REDIS_URL=${REDIS_URL}
    - INTELLICARE_MULTI_TENANT_ENABLED=true   # MUDAR para true
    # ADICIONAR:
    - KEYCLOAK_URL=https://auth.intellicare.ia.br
    - KEYCLOAK_REALM=intellicare
    - KEYCLOAK_CLIENT_ID=intellicare-gestor
    - KEYCLOAK_CLIENT_SECRET=${GESTOR_KEYCLOAK_CLIENT_SECRET}
```

---

## 5. Estrutura de rotas (estado esperado)

Todas as rotas exigem `Depends(require_tenant_gestor)`.
Todas as queries filtram por `tenant_id`.

```
GET  /api/v1/gestor/health         → HealthCheck (público)
GET  /api/v1/gestor/info           → ModuleInfo (público)

# Dashboard
GET  /api/v1/gestor/dashboard      → resumo do tenant (contagens, alertas)

# Unidades
GET  /api/v1/gestor/units          → lista unidades do tenant
POST /api/v1/gestor/units          → cria unidade
GET  /api/v1/gestor/units/{id}     → detalhes
PATCH /api/v1/gestor/units/{id}    → edita

# Profissionais
GET  /api/v1/gestor/professionals  → lista profissionais do tenant
POST /api/v1/gestor/professionals  → cadastra profissional
GET  /api/v1/gestor/professionals/{id}  → detalhes
PATCH /api/v1/gestor/professionals/{id} → edita

# Alocações
GET  /api/v1/gestor/allocations                        → todas as alocações
POST /api/v1/gestor/allocations                        → cria alocação
DELETE /api/v1/gestor/allocations/{id}                 → remove alocação
GET  /api/v1/gestor/units/{id}/professionals           → profissionais de uma unidade
GET  /api/v1/gestor/professionals/{id}/units           → unidades de um profissional

# Usuários do portal
GET  /api/v1/gestor/users          → lista usuários com acesso
POST /api/v1/gestor/users          → cria acesso (cria user no Keycloak)
PATCH /api/v1/gestor/users/{id}    → edita (ativa/desativa)
DELETE /api/v1/gestor/users/{id}   → remove acesso

# Roles
GET  /api/v1/gestor/roles          → lista roles do tenant
POST /api/v1/gestor/roles          → cria role
PATCH /api/v1/gestor/roles/{id}    → edita

# Configurações
GET  /api/v1/gestor/settings       → configurações do tenant
PATCH /api/v1/gestor/settings      → atualiza configurações

# Auditoria
GET  /api/v1/gestor/audit          → logs de auditoria do tenant
```

---

## 6. Interface do gestor — decisão pendente

### Opção A: Dashboard HTML próprio (recomendado para Fase 1)

Criar `gestor/templates/dashboard.html` seguindo o mesmo padrão do admin:
- Usa Keycloak.js para auth com `realm: 'intellicare'`
- Sidebar com: Dashboard, Unidades, Profissionais, Alocações, Usuários, Configurações
- Chamadas API para os endpoints do gestor

**Vantagem:** funciona independente do portal, pode ser entregue primeiro.

### Opção B: Páginas no portal React (definitivo)

O portal em `intellicare-portal` adiciona seção `/gestor/*` com as páginas.
O `gestor.intellicare.ia.br` serve o portal compilado com rota de gestor.

**Vantagem:** UX consistente com o resto da plataforma.
**Desvantagem:** depende do portal estar funcional.

**Decisão:** Eduardo define. Para esta demanda (DEM-002), implementar Opção A
como solução temporária funcional.

---

## 7. Testes mínimos esperados

```bash
# Sem token — deve retornar 401
curl https://gestor.intellicare.ia.br/api/v1/gestor/units

# Com token de PLATFORM_ADMIN — deve retornar 403 (role errada)
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     https://gestor.intellicare.ia.br/api/v1/gestor/units

# Com token de TENANT_GESTOR — deve retornar 200 (só dados do tenant)
curl -H "Authorization: Bearer $GESTOR_TOKEN" \
     https://gestor.intellicare.ia.br/api/v1/gestor/units

# Isolamento de tenant:
# Gestor do tenant A NÃO deve ver dados do tenant B
```
