# DEM-031 — Gestão Completa: Especificação Técnica

## 1. Banco de Dados — schema do tenant (`tenant_{slug}`)

### Arquivo: `db/tenant_migrations/005_gestao_completa.sql`

```sql
-- ============================================================
-- Unidades de Saúde (schema do tenant)
-- ============================================================
CREATE TABLE IF NOT EXISTS units (
    id              SERIAL PRIMARY KEY,
    name            TEXT        NOT NULL,
    type            TEXT        NOT NULL
                                CHECK (type IN ('ubs','hospital','clinic','secretary','other')),
    cnes            TEXT,
    address         TEXT,
    city            TEXT,
    state           CHAR(2),
    phone           TEXT,
    email           TEXT,
    manager_user_id TEXT,       -- keycloak_id do gestor responsável
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','inactive')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Alocação de profissionais em unidades
CREATE TABLE IF NOT EXISTS unit_professionals (
    unit_id         INTEGER     NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    professional_id INTEGER     NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    role_in_unit    TEXT,
    workload_hours  INTEGER,    -- horas semanais
    allocated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (unit_id, professional_id)
);

-- ============================================================
-- Usuários do Tenant
-- ============================================================
CREATE TABLE IF NOT EXISTS tenant_users (
    id              SERIAL PRIMARY KEY,
    keycloak_id     TEXT        UNIQUE,
    email           TEXT        NOT NULL UNIQUE,
    name            TEXT        NOT NULL,
    role            TEXT        NOT NULL DEFAULT 'clinico'
                                CHECK (role IN ('gestor','clinico','recepcionista')),
    unit_id         INTEGER     REFERENCES units(id) ON DELETE SET NULL,
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','inactive')),
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Nota:** `professionals` já existe em `tenant_migrations/004_cuidado_tables.sql`. Verificar se existe antes de referenciar; se não, criar tabela mínima:
```sql
CREATE TABLE IF NOT EXISTS professionals (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    specialty   TEXT,
    crm         TEXT,
    status      TEXT NOT NULL DEFAULT 'active'
);
```

---

## 2. Backend — `modules/gestor/`

### 2.1 Novos endpoints (`router.py`)

```python
# Unidades
GET    /gestor/units                           → list_units
POST   /gestor/units                           → create_unit
GET    /gestor/units/{unit_id}                 → get_unit
PATCH  /gestor/units/{unit_id}                 → update_unit
PATCH  /gestor/units/{unit_id}/status          → toggle_unit_status

# Alocação de profissionais
GET    /gestor/units/{unit_id}/professionals   → list_unit_professionals
POST   /gestor/units/{unit_id}/professionals   → allocate_professional
DELETE /gestor/units/{unit_id}/professionals/{prof_id} → remove_professional

# Usuários do tenant
GET    /gestor/users                           → list_tenant_users
POST   /gestor/users                           → create_tenant_user  (convida via Keycloak)
PATCH  /gestor/users/{user_id}                 → update_tenant_user
DELETE /gestor/users/{user_id}                 → delete_tenant_user
```

### 2.2 Schemas novos (`schemas.py`)

```python
class UnitCreate(BaseModel):
    name: str
    type: Literal['ubs','hospital','clinic','secretary','other']
    cnes: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    phone: str | None = None
    email: str | None = None
    manager_user_id: str | None = None

class UnitOut(BaseModel):
    id: int
    name: str
    type: str
    cnes: str | None
    city: str | None
    state: str | None
    manager_user_id: str | None
    status: str
    professional_count: int = 0
    patient_count: int = 0

class TenantUserCreate(BaseModel):
    email: str
    name: str
    role: Literal['gestor', 'clinico', 'recepcionista'] = 'clinico'
    unit_id: int | None = None

class TenantUserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    unit_id: int | None
    unit_name: str | None
    status: str
    last_login_at: datetime | None
    created_at: datetime
```

### 2.3 Contexto de tenant

Todos os endpoints do gestor já usam `TenantContext` com `SET search_path = tenant_{slug}`. As novas queries seguem o mesmo padrão.

---

## 3. Frontend — `frontend/GestorUI/`

### 3.1 Arquivos a criar

```
src/
├── hooks/
│   ├── useUnits.ts            # CRUD unidades + alocação profissionais
│   └── useTenantUsers.ts      # CRUD usuários do tenant
├── pages/
│   ├── UnitsPage.tsx          # listagem + modal add/edit
│   ├── UnitDetailPage.tsx     # detalhe + abas Equipe/Pacientes
│   └── TenantUsersPage.tsx    # listagem + modal convite
```

### 3.2 Sidebar — atualizar `App.tsx`

```tsx
{ label: 'Unidades',  icon: IconBuilding,    path: '/units' },
{ label: 'Usuários',  icon: IconUsers,       path: '/users' },
```

### 3.3 UnitsPage.tsx

```
┌────────────────────────────────────────────┐
│ Unidades                    [+ Adicionar]  │
├─────────────┬──────────┬───────┬───────────┤
│ Nome        │ Tipo     │ Cidade│ Status    │
├─────────────┼──────────┼───────┼───────────┤
│ UBS Centro  │ UBS      │ SP    │ ● ativa   │
│ Hosp. Alfa  │ Hospital │ SP    │ ● ativa   │
└─────────────┴──────────┴───────┴───────────┘
```

### 3.4 TenantUsersPage.tsx

```
┌──────────────────────────────────────────────┐
│ Usuários do Tenant              [+ Convidar] │
├────────────────┬─────────┬────────┬──────────┤
│ Nome / E-mail  │ Perfil  │Unidade │ Status   │
├────────────────┼─────────┼────────┼──────────┤
│ Dr. Silva      │ clinico │ UBS Ctr│ ● ativo  │
│ Maria G.       │ gestor  │  —     │ ● ativo  │
└────────────────┴─────────┴────────┴──────────┘
```

### 3.5 Dashboard — atualizar

Adicionar card:
```
┌─────────────────────────────┐
│ 🏥 Unidades                 │
│ 3 unidades ativas           │
│ 12 profissionais alocados   │
└─────────────────────────────┘
```

---

## 4. Sequência de execução

```bash
# 1. Migration do tenant
docker exec -i intellicare-postgres psql -U intellicare intellicare \
  -c "SET search_path = tenant_alfa;" \
  < db/tenant_migrations/005_gestao_completa.sql

# 2. Backend (schemas → service → router) + rebuild
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  build intellicare-service && \
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  up -d intellicare-service

# 3. Frontend (hooks → pages → App.tsx) + build
cd frontend/GestorUI && npx vite build

# 4. Restart
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  restart intellicare-service
```

---

## 5. Checklist de entrega

- [ ] Migration `005_gestao_completa.sql` aplicada
- [ ] Endpoints de Unidades funcionando (CRUD + alocação)
- [ ] Endpoints de Usuários do Tenant funcionando
- [ ] GestorUI: UnitsPage + TenantUsersPage na sidebar
- [ ] Dashboard com card de Unidades
- [ ] Build sem erros
- [ ] Commit: `feat(DEM-031): gestao completa - unidades e usuarios`
