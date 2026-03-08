# ESPECIFICAÇÃO TÉCNICA — intellicare-admin

**Módulo:** intellicare-admin
**Versão:** 1.0
**Data:** 2026-03-08
**Status:** Aprovada para implementação

---

## 1. Correções obrigatórias (antes de qualquer feature nova)

### 1.1 pyproject.toml — dependências ausentes

Adicionar ao `[tool.poetry.dependencies]`:
```toml
intellicare-core = {path = "../intellicare-core", develop = true}
intellicare-auth = {path = "../intellicare-auth", develop = true}
```

Remover:
```toml
python-keycloak = "^3.0.0"   # substituído por intellicare-auth
```

### 1.2 app.py — adicionar configure_auth e tenant resolver

```python
# lifespan
from intellicare_core.tenant import init_tenant_resolver
from intellicare_auth.fastapi import configure_auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_tenant_resolver()           # ADICIONAR
    # ... resto do lifespan existente
    yield

# após criar o app
configure_auth(app, secrets_path="keycloak_client_secrets.json")  # ADICIONAR
```

### 1.3 db/session.py — usar TenantAwareSessionFactory

```python
# REMOVER o engine direto:
# engine = create_async_engine(settings.database_url)
# AsyncSessionLocal = sessionmaker(engine, ...)

# USAR:
from intellicare_core.tenant import TenantAwareSessionFactory
session_factory = TenantAwareSessionFactory(settings.database_url)
```

### 1.4 dashboard.html — corrigir realm

```javascript
// ANTES (errado):
var keycloak = new Keycloak({
    url: 'https://auth.intellicare.ia.br',
    realm: 'bemcuidar',          // ← ERRADO
    clientId: 'intellicare-admin'
});

// DEPOIS (correto):
var keycloak = new Keycloak({
    url: 'https://auth.intellicare.ia.br',
    realm: 'intellicare',        // ← CORRETO
    clientId: 'intellicare-admin'
});
```

### 1.5 deps.py — corrigir importação

```python
# REMOVER:
# from intellicare_auth.client import KeycloakClient
# kc_client = KeycloakClient()

# USAR padrão intellicare-auth:
from intellicare_auth.fastapi.deps import require_role

async def require_platform_admin(
    payload: dict = Depends(require_role("PLATFORM_ADMIN"))
) -> dict:
    return payload
```

---

## 2. Configuração Keycloak

### Pré-requisito: realm `intellicare` deve existir

```bash
# Criar realm (via Keycloak Admin Console ou kcadm.sh)
# URL: https://auth.intellicare.ia.br/admin/master/console

# Realm: intellicare
# Display name: IntelliCare Platform
# Login theme: intellicare (ou default)
```

### Criar cliente `intellicare-admin`

```
Client ID: intellicare-admin
Client Type: confidential (OpenID Connect)
Valid Redirect URIs: https://admin.intellicare.ia.br/*
Web Origins: https://admin.intellicare.ia.br
Service Account Roles: true
```

### Criar roles no realm `intellicare`

```
PLATFORM_ADMIN  — acesso total ao admin
TENANT_GESTOR   — acesso ao gestor (não ao admin)
PROFISSIONAL    — acesso ao portal
PACIENTE        — acesso ao portal (área do paciente)
```

### keycloak_client_secrets.json

Gerar no Keycloak → Clients → intellicare-admin → Credentials → Client Secret:
```json
{
  "realm": "intellicare",
  "auth-server-url": "https://auth.intellicare.ia.br",
  "resource": "intellicare-admin",
  "credentials": {
    "secret": "<gerado no Keycloak>"
  }
}
```

Este arquivo deve estar no diretório raiz do módulo em runtime.
**NÃO commitar no git** — adicionar ao `.gitignore`.

---

## 3. Banco de dados

### Schema dedicado

```
PostgreSQL database: intellicare_db
Schema: intellicare_admin
```

### Tabelas existentes (verificar migrations)

```sql
-- tenants
CREATE TABLE intellicare_admin.tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    cnpj        VARCHAR(14) UNIQUE,
    email       VARCHAR(255) NOT NULL,
    plan_id     UUID REFERENCES plans(id),
    status      VARCHAR(20) DEFAULT 'trial',  -- trial, active, suspended, cancelled
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    suspended_at TIMESTAMPTZ
);

-- plans, billing, audit, estabelecimentos, secretarias
-- (verificar arquivos de migration em migrations/)
```

### Alembic

```bash
# Aplicar migrations pendentes
cd intellicare-admin
alembic upgrade head

# Gerar nova migration após alterar models
alembic revision --autogenerate -m "descricao"
```

---

## 4. Variáveis de ambiente

No `docker-compose.full.yml`, adicionar as variáveis ausentes:

```yaml
admin:
  environment:
    - INTELLICARE_ADMIN_DATABASE_URL=${INTELLICARE_ADMIN_DATABASE_URL}
    - ADMIN_DATABASE_SCHEMA=intellicare_admin
    - INTELLICARE_REDIS_URL=${REDIS_URL}
    # ADICIONAR:
    - KEYCLOAK_URL=https://auth.intellicare.ia.br
    - KEYCLOAK_REALM=intellicare
    - KEYCLOAK_CLIENT_ID=intellicare-admin
    - KEYCLOAK_CLIENT_SECRET=${ADMIN_KEYCLOAK_CLIENT_SECRET}
```

No `config.py`, garantir que essas vars são lidas:

```python
class AdminConfig(BaseModuleConfig):
    keycloak_url: str = Field(..., alias="KEYCLOAK_URL")
    keycloak_realm: str = Field(default="intellicare", alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(..., alias="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: str = Field(..., alias="KEYCLOAK_CLIENT_SECRET")
```

---

## 5. Estrutura de rotas (estado esperado)

```
GET  /                          → dashboard.html (autenticado via Keycloak.js)
GET  /api/v1/health             → HealthCheck (público)
GET  /api/v1/info               → ModuleInfo (público)

# Tenants
GET  /api/v1/admin/tenants              → lista todos
POST /api/v1/admin/tenants              → cria tenant + provisiona recursos
GET  /api/v1/admin/tenants/{id}         → detalhes do tenant
PATCH /api/v1/admin/tenants/{id}        → edita dados
POST /api/v1/admin/tenants/{id}/suspend → suspende
POST /api/v1/admin/tenants/{id}/activate → ativa

# Gestores
GET  /api/v1/admin/gestores             → lista gestores (todos os tenants)
POST /api/v1/admin/gestores             → cria gestor (cria user no Keycloak)
DELETE /api/v1/admin/gestores/{id}      → remove acesso de gestor

# Planos
GET  /api/v1/plans              → lista planos
POST /api/v1/plans              → cria plano
PATCH /api/v1/plans/{id}        → edita plano

# Billing
GET  /api/v1/billing            → histórico de faturamento
POST /api/v1/billing            → registra pagamento

# Módulos por tenant
GET  /api/v1/admin/tenants/{id}/modules       → módulos do tenant
PATCH /api/v1/admin/tenants/{id}/modules      → habilita/desabilita módulo

# Auditoria
GET  /api/v1/admin/audit        → logs de auditoria da plataforma
```

Todas as rotas (exceto health e info) exigem `Depends(require_platform_admin)`.

---

## 6. Provisioning automático de tenant

Quando um tenant é criado via `POST /api/v1/admin/tenants`, o `provisioning_service`
deve executar automaticamente:

```python
async def provision_tenant(tenant_id: str, tenant_slug: str):
    # 1. Criar schema no PostgreSQL
    await db.execute(f"CREATE SCHEMA IF NOT EXISTS {tenant_slug}")

    # 2. Criar prefixo Redis para o tenant
    # (automático via TenantRedisClient — só registrar o slug)

    # 3. Criar grupo no Keycloak para o tenant
    # kc.create_group(name=tenant_slug, realm="intellicare")

    # 4. Registrar tenant no intellicare-core para resolução
    await tenant_resolver.register(tenant_id, tenant_slug)
```

---

## 7. Testes mínimos esperados

```bash
# Iniciar módulo
uvicorn admin.api.app:app --reload --port 8010

# Health check (deve retornar 200 sem token)
curl https://admin.intellicare.ia.br/api/v1/health

# Rota protegida sem token (deve retornar 401)
curl https://admin.intellicare.ia.br/api/v1/admin/tenants

# Dashboard (deve redirecionar para login Keycloak)
# Abrir no browser: https://admin.intellicare.ia.br
```
