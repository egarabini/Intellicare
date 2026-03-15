# DEM-030 — Administrativo Completo: Especificação Técnica

## Visão geral

| Camada | Escopo |
|--------|--------|
| Backend | 4 novos grupos de endpoints em `modules/admin/` |
| Banco | 4 novas tabelas em `db/platform_migrations/` |
| Frontend | 4 novas páginas + sidebar atualizada em `frontend/AdminUI/` |

---

## 1. Banco de Dados

### Arquivo: `db/platform_migrations/003_admin_completo.sql`

```sql
-- ============================================================
-- Servidores de infraestrutura
-- ============================================================
CREATE TABLE IF NOT EXISTS public.servers (
    id          SERIAL PRIMARY KEY,
    name        TEXT        NOT NULL,
    type        TEXT        NOT NULL CHECK (type IN ('vps','dedicated','cloud')),
    provider    TEXT        NOT NULL,
    region      TEXT        NOT NULL,
    hostname    TEXT,
    vcpu        INTEGER     NOT NULL CHECK (vcpu > 0),
    ram_gb      INTEGER     NOT NULL CHECK (ram_gb > 0),
    disk_gb     INTEGER     NOT NULL CHECK (disk_gb > 0),
    cost_brl    INTEGER     NOT NULL DEFAULT 0,  -- centavos
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active','inactive','maintenance')),
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Módulos da plataforma
-- ============================================================
CREATE TABLE IF NOT EXISTS public.platform_modules (
    id          SERIAL PRIMARY KEY,
    slug        TEXT        NOT NULL UNIQUE,
    name        TEXT        NOT NULL,
    description TEXT,
    version     TEXT        NOT NULL DEFAULT '1.0.0',
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active','inactive','dev')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Módulos habilitados por tenant
CREATE TABLE IF NOT EXISTS public.tenant_modules (
    tenant_slug TEXT        NOT NULL REFERENCES public.tenants(slug) ON DELETE CASCADE,
    module_slug TEXT        NOT NULL REFERENCES public.platform_modules(slug) ON DELETE CASCADE,
    enabled     BOOLEAN     NOT NULL DEFAULT true,
    enabled_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_slug, module_slug)
);

-- ============================================================
-- Despesas da plataforma
-- ============================================================
CREATE TABLE IF NOT EXISTS public.expenses (
    id          SERIAL PRIMARY KEY,
    category    TEXT        NOT NULL
                            CHECK (category IN ('infrastructure','license','personnel','other')),
    description TEXT        NOT NULL,
    amount_brl  INTEGER     NOT NULL CHECK (amount_brl > 0),  -- centavos
    expense_date DATE       NOT NULL,
    tenant_slug TEXT        REFERENCES public.tenants(slug) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Usuários administrativos (roles do painel admin)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.admin_users (
    id              SERIAL PRIMARY KEY,
    keycloak_id     TEXT        UNIQUE,
    email           TEXT        NOT NULL UNIQUE,
    name            TEXT        NOT NULL,
    role            TEXT        NOT NULL DEFAULT 'coordenador'
                                CHECK (role IN ('admin','financ','coordenador')),
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','inactive')),
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed: módulos padrão da plataforma
INSERT INTO public.platform_modules (slug, name, description, version, status) VALUES
    ('admin',    'Administrativo',  'Gestão da plataforma',          '3.0.0', 'active'),
    ('gestor',   'Gestão',          'Gestão de unidades e usuários',  '3.0.0', 'active'),
    ('cuidado',  'Clínico',         'Prontuário e atendimento',       '3.0.0', 'active'),
    ('florence', 'Florence AI',     'Assistente IA de saúde',         '1.0.0', 'dev'),
    ('oswaldo',  'Oswaldo BI',      'Business Intelligence de saúde', '1.0.0', 'dev')
ON CONFLICT (slug) DO NOTHING;
```

**Como aplicar:** adicionar a execução deste arquivo ao `init.sql` ou rodar manualmente:
```bash
docker exec -i intellicare-postgres psql -U intellicare intellicare < db/platform_migrations/003_admin_completo.sql
```

---

## 2. Backend — `modules/admin/`

### 2.1 Schemas (`schemas.py`) — adicionar ao arquivo existente

```python
# ---------- Servidores ----------
class ServerCreate(BaseModel):
    name: str
    type: Literal['vps', 'dedicated', 'cloud']
    provider: str
    region: str
    hostname: str | None = None
    vcpu: int = Field(gt=0)
    ram_gb: int = Field(gt=0)
    disk_gb: int = Field(gt=0)
    cost_brl: int = Field(ge=0, description="Centavos")
    status: Literal['active', 'inactive', 'maintenance'] = 'active'
    notes: str | None = None

class ServerUpdate(BaseModel):
    name: str | None = None
    status: Literal['active', 'inactive', 'maintenance'] | None = None
    cost_brl: int | None = None
    notes: str | None = None

class ServerOut(BaseModel):
    id: int
    name: str
    type: str
    provider: str
    region: str
    hostname: str | None
    vcpu: int
    ram_gb: int
    disk_gb: int
    cost_brl: int
    cost_brl_display: float   # cost_brl / 100
    status: str
    notes: str | None
    created_at: datetime

# ---------- Módulos ----------
class ModuleStatusUpdate(BaseModel):
    status: Literal['active', 'inactive', 'dev']

class TenantModuleUpdate(BaseModel):
    enabled: bool

class ModuleOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None
    version: str
    status: str
    tenant_count: int = 0   # quantos tenants têm ativo

# ---------- Financeiro ----------
class ExpenseCreate(BaseModel):
    category: Literal['infrastructure', 'license', 'personnel', 'other']
    description: str
    amount_brl: int = Field(gt=0, description="Centavos")
    expense_date: date
    tenant_slug: str | None = None

class ExpenseOut(BaseModel):
    id: int
    category: str
    description: str
    amount_brl: int
    amount_brl_display: float
    expense_date: date
    tenant_slug: str | None
    created_at: datetime

class InvoiceStatusUpdate(BaseModel):
    status: Literal['paid', 'overdue', 'cancelled']
    paid_at: datetime | None = None

class FinanceiroDashboard(BaseModel):
    receita_mes: float
    despesa_mes: float
    resultado_mes: float
    inadimplencia: float
    historico: list[dict]   # [{mes, receita, despesa}] últimos 6 meses

# ---------- Usuários Admin ----------
class AdminUserCreate(BaseModel):
    email: str
    name: str
    role: Literal['admin', 'financ', 'coordenador'] = 'coordenador'

class AdminUserUpdate(BaseModel):
    role: Literal['admin', 'financ', 'coordenador'] | None = None
    status: Literal['active', 'inactive'] | None = None

class AdminUserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    status: str
    last_login_at: datetime | None
    created_at: datetime
```

### 2.2 Service (`service.py`) — adicionar métodos à classe `AdminService`

```python
# ---------- Servidores ----------
async def list_servers(self) -> list[dict]: ...
async def create_server(self, payload: ServerCreate, actor: str) -> dict: ...
async def update_server(self, server_id: int, payload: ServerUpdate, actor: str) -> dict: ...
async def delete_server(self, server_id: int, actor: str) -> None: ...

# ---------- Módulos ----------
async def list_modules(self) -> list[dict]: ...
async def update_module_status(self, slug: str, payload: ModuleStatusUpdate, actor: str) -> dict: ...
async def list_tenant_modules(self, tenant_slug: str) -> list[dict]: ...
async def update_tenant_module(self, tenant_slug: str, module_slug: str, payload: TenantModuleUpdate, actor: str) -> dict: ...

# ---------- Financeiro ----------
async def get_financeiro_dashboard(self) -> dict: ...
async def list_invoices(self, page: int, size: int, status: str | None, tenant_slug: str | None) -> dict: ...
async def update_invoice_status(self, invoice_id: int, payload: InvoiceStatusUpdate, actor: str) -> dict: ...
async def list_expenses(self, page: int, size: int) -> dict: ...
async def create_expense(self, payload: ExpenseCreate, actor: str) -> dict: ...
async def delete_expense(self, expense_id: int, actor: str) -> None: ...

# ---------- Usuários Admin ----------
async def list_admin_users(self) -> list[dict]: ...
async def create_admin_user(self, payload: AdminUserCreate, actor: str) -> dict: ...
async def update_admin_user(self, user_id: int, payload: AdminUserUpdate, actor: str) -> dict: ...
async def delete_admin_user(self, user_id: int, actor: str) -> None: ...
```

**Nota:** todos os métodos que alteram dados devem chamar `self._audit(conn, actor, ação, entidade, id, payload)`.

### 2.3 Router (`router.py`) — adicionar ao arquivo existente

```python
# Servidores
GET    /admin/servers                          → list_servers
POST   /admin/servers                          → create_server
PATCH  /admin/servers/{server_id}              → update_server
DELETE /admin/servers/{server_id}              → delete_server

# Módulos
GET    /admin/modules                          → list_modules
PATCH  /admin/modules/{slug}/status            → update_module_status
GET    /admin/tenants/{slug}/modules           → list_tenant_modules
PATCH  /admin/tenants/{slug}/modules/{module}  → update_tenant_module

# Financeiro
GET    /admin/financeiro/dashboard             → get_financeiro_dashboard
GET    /admin/invoices                         → list_invoices (?status=&tenant_slug=&page=&size=)
PATCH  /admin/invoices/{invoice_id}/status     → update_invoice_status
GET    /admin/expenses                         → list_expenses (?page=&size=)
POST   /admin/expenses                         → create_expense
DELETE /admin/expenses/{expense_id}            → delete_expense

# Usuários administrativos
GET    /admin/users                            → list_admin_users
POST   /admin/users                            → create_admin_user
PATCH  /admin/users/{user_id}                  → update_admin_user
DELETE /admin/users/{user_id}                  → delete_admin_user
```

---

## 3. Frontend — `frontend/AdminUI/`

### 3.1 Estrutura de arquivos a criar

```
src/
├── hooks/
│   ├── useServers.ts          # CRUD servidores
│   ├── useModules.ts          # módulos plataforma + tenant_modules
│   ├── useFinanceiro.ts       # dashboard + invoices + expenses
│   └── useAdminUsers.ts       # CRUD usuários admin
├── pages/
│   ├── ServersPage.tsx        # listagem + modal add/edit
│   ├── ModulesPage.tsx        # listagem + status toggle
│   ├── FinanceiroPage.tsx     # dashboard + tabs faturas/despesas
│   └── AdminUsersPage.tsx     # listagem + modal convite
```

### 3.2 Sidebar — atualizar `App.tsx`

Adicionar ao `navLinks` existente (após Auditoria):

```tsx
{ label: 'Servidores',  icon: IconServer,      path: '/servers'   },
{ label: 'Módulos',     icon: IconPuzzle,       path: '/modules'   },
{ label: 'Financeiro',  icon: IconCurrencyReal, path: '/financeiro'},
{ label: 'Usuários',    icon: IconUsers,        path: '/users'     },
```

### 3.3 ServersPage.tsx

```
Layout:
┌─────────────────────────────────────────────┐
│ Servidores             [+ Adicionar]         │
├──────┬──────────┬──────┬──────┬─────────────┤
│ Nome │ Tipo     │ CPU  │ RAM  │ Custo/mês   │ Status │ Ações │
├──────┴──────────┴──────┴──────┴─────────────┤
│ VPS-01  VPS  Hetzner  4vCPU  8GB  R$ 120,00│ ● ativo│  ✏ 🗑 │
└─────────────────────────────────────────────┘

Modal Adicionar/Editar:
- Nome, Tipo (select), Provedor, Região, IP/Hostname
- vCPU, RAM (GB), Disco (GB), Custo mensal (R$)
- Status (select), Observações (textarea)
```

### 3.4 ModulesPage.tsx

```
Layout:
┌──────────────────────────────────────────────────┐
│ Módulos da Plataforma                             │
├──────────────┬──────────┬──────────┬─────────────┤
│ Módulo       │ Versão   │ Tenants  │ Status       │
├──────────────┼──────────┼──────────┼─────────────┤
│ Clínico      │ 3.0.0    │ 3 ativos │ ● ativo  [▼]│
│ Florence AI  │ 1.0.0    │ —        │ ⚙ dev    [▼]│
└──────────────────────────────────────────────────┘

Na tela do tenant (detalhe), nova aba "Módulos":
┌────────────────────────────────────┐
│ Módulo       Status Global  Tenant │
│ Administrativo  ● ativo    [ON] ●  │
│ Gestão          ● ativo    [ON] ●  │
│ Clínico         ● ativo    [ON] ●  │
│ Florence AI     ⚙ dev      [--] ○  │  ← desabilitado
└────────────────────────────────────┘
```

### 3.5 FinanceiroPage.tsx

```
Layout (3 tabs: Dashboard | Faturas | Despesas):

[Dashboard]
┌──────────┬──────────┬──────────┬──────────────┐
│ Receita  │ Despesa  │Resultado │ Inadimplência │
│ R$ 4.800 │ R$ 1.200 │ R$ 3.600 │   R$ 600      │
└──────────┴──────────┴──────────┴──────────────┘
[Gráfico linha: Receita vs Despesa — últimos 6 meses]

[Faturas]
Filtros: Status | Tenant | Mês
Tabela: Tenant | Valor | Vencimento | Status | Pago em | Ações

[Despesas]
[+ Adicionar Despesa]
Tabela: Categoria | Descrição | Valor | Data | Tenant | Ações
```

### 3.6 AdminUsersPage.tsx

```
Layout:
┌────────────────────────────────────────────┐
│ Usuários Administrativos    [+ Convidar]   │
├──────────────┬──────────┬──────────────────┤
│ Nome / E-mail│ Perfil   │ Status│ Último   │
├──────────────┼──────────┼───────┼──────────┤
│ Eduardo G.   │ admin    │ ativo │ agora    │
│ Carlos F.    │ financ   │ ativo │ 2 dias   │
└──────────────┴──────────┴───────┴──────────┘

Modal Convidar:
- Nome*, E-mail*, Perfil* (select: admin/financ/coordenador)
→ Cria usuário no Keycloak com role PLATFORM_ADMIN + sub-role salva em admin_users
→ Envia e-mail de boas-vindas com senha temporária (via Keycloak)
```

---

## 4. Dashboard principal — atualizar `useTenants.ts` + `Dashboard.tsx`

Adicionar aos stats existentes:
```typescript
// GET /admin/servers → calcular total custo
servers_active: number
infra_cost_monthly: number  // soma de cost_brl de todos servers ativos / 100
```

Adicionar card no Dashboard:
```
┌───────────────────────────────┐
│ 🖥  Infraestrutura            │
│ 4 servidores ativos           │
│ Custo mensal: R$ 1.840,00     │
└───────────────────────────────┘
```

---

## 5. Sequência de execução para o dev

```bash
# 1. Aplicar migration
docker exec -i intellicare-postgres psql -U intellicare intellicare \
  < db/platform_migrations/003_admin_completo.sql

# 2. Implementar backend (schemas → service → router)
# Arquivo: modules/admin/schemas.py  → adicionar novos schemas
# Arquivo: modules/admin/service.py  → adicionar novos métodos
# Arquivo: modules/admin/router.py   → adicionar novos endpoints

# 3. Rebuild do container (Python mudou)
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  build intellicare-service

# 4. Implementar frontend
# Criar hooks: useServers.ts, useModules.ts, useFinanceiro.ts, useAdminUsers.ts
# Criar páginas: ServersPage, ModulesPage, FinanceiroPage, AdminUsersPage
# Atualizar: App.tsx (sidebar + rotas)

# 5. Build frontend
cd frontend/AdminUI && npx vite build

# 6. Restart (volume mount — não precisa rebuild)
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  restart intellicare-service
```

---

## 6. Checklist de entrega

- [ ] Migration `003_admin_completo.sql` aplicada sem erros
- [ ] Seed de módulos inserido (`platform_modules`)
- [ ] Endpoints de Servidores respondendo (CRUD completo)
- [ ] Endpoints de Módulos respondendo (platform + por tenant)
- [ ] Endpoints de Financeiro respondendo (dashboard, invoices, expenses)
- [ ] Endpoints de Usuários Admin respondendo (CRUD + Keycloak)
- [ ] AdminUI: 4 novas páginas na sidebar
- [ ] Dashboard com card de infraestrutura
- [ ] Auditoria registra todas as ações novas
- [ ] Build sem erros: `npx vite build`
- [ ] Commit: `feat(DEM-030): administrativo completo`
