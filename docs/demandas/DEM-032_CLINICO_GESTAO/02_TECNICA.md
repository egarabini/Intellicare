# DEM-032 — Clínico Gestão: Especificação Técnica

## 1. Banco de Dados — schema do tenant

### Arquivo: `db/tenant_migrations/006_clinico_gestao.sql`

```sql
-- ============================================================
-- Profissionais de Saúde
-- (pode já existir parcialmente — usar CREATE TABLE IF NOT EXISTS)
-- ============================================================
CREATE TABLE IF NOT EXISTS professionals (
    id              SERIAL PRIMARY KEY,
    name            TEXT        NOT NULL,
    council_type    TEXT        NOT NULL
                                CHECK (council_type IN ('CRM','COREN','CRO','CRP','CREFITO','other')),
    council_number  TEXT        NOT NULL,
    specialty       TEXT        NOT NULL,
    unit_id         INTEGER     REFERENCES units(id) ON DELETE SET NULL,
    keycloak_id     TEXT        UNIQUE,
    phone           TEXT,
    email           TEXT,
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','inactive')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Grupos de Profissionais
-- ============================================================
CREATE TABLE IF NOT EXISTS professional_groups (
    id              SERIAL PRIMARY KEY,
    name            TEXT        NOT NULL,
    specialty       TEXT,
    unit_id         INTEGER     REFERENCES units(id) ON DELETE SET NULL,
    description     TEXT,
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','inactive')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Membros do grupo
CREATE TABLE IF NOT EXISTS group_members (
    group_id        INTEGER     NOT NULL REFERENCES professional_groups(id) ON DELETE CASCADE,
    professional_id INTEGER     NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, professional_id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_professionals_unit   ON professionals (unit_id);
CREATE INDEX IF NOT EXISTS idx_professionals_status ON professionals (status);
CREATE INDEX IF NOT EXISTS idx_groups_unit          ON professional_groups (unit_id);
```

---

## 2. Backend — `modules/cuidado/`

### 2.1 Novos endpoints (`router.py`)

```python
# Grupos de Profissionais
GET    /cuidado/groups                         → list_groups
POST   /cuidado/groups                         → create_group
GET    /cuidado/groups/{group_id}              → get_group
PATCH  /cuidado/groups/{group_id}              → update_group
PATCH  /cuidado/groups/{group_id}/status       → toggle_group_status
GET    /cuidado/groups/{group_id}/members      → list_group_members
POST   /cuidado/groups/{group_id}/members      → add_member      body: {professional_id}
DELETE /cuidado/groups/{group_id}/members/{id} → remove_member

# Profissionais
GET    /cuidado/professionals                  → list_professionals (?unit_id=&specialty=&group_id=&status=)
POST   /cuidado/professionals                  → create_professional
GET    /cuidado/professionals/{prof_id}        → get_professional
PATCH  /cuidado/professionals/{prof_id}        → update_professional
PATCH  /cuidado/professionals/{prof_id}/status → toggle_professional_status

# Usuários do Clínico (read-only — lê de tenant_users)
GET    /cuidado/clinical-users                 → list_clinical_users
```

### 2.2 Schemas (`schemas.py`) — adicionar

```python
class ProfessionalCreate(BaseModel):
    name: str
    council_type: Literal['CRM','COREN','CRO','CRP','CREFITO','other']
    council_number: str
    specialty: str
    unit_id: int | None = None
    phone: str | None = None
    email: str | None = None

class ProfessionalOut(BaseModel):
    id: int
    name: str
    council_type: str
    council_number: str
    specialty: str
    unit_id: int | None
    unit_name: str | None
    groups: list[str] = []     # nomes dos grupos
    status: str
    keycloak_id: str | None

class GroupCreate(BaseModel):
    name: str
    specialty: str | None = None
    unit_id: int | None = None
    description: str | None = None

class GroupOut(BaseModel):
    id: int
    name: str
    specialty: str | None
    unit_id: int | None
    unit_name: str | None
    description: str | None
    status: str
    member_count: int = 0
```

---

## 3. Frontend — `frontend/ClinicoUI/`

### 3.1 Arquivos a criar

```
src/
├── hooks/
│   ├── useGroups.ts           # CRUD grupos + membros
│   ├── useProfessionals.ts    # CRUD profissionais
│   └── useClinicalUsers.ts    # listagem read-only
├── pages/
│   ├── GroupsPage.tsx         # listagem grupos + modal add/edit
│   ├── GroupDetailPage.tsx    # detalhe grupo + membros
│   ├── ProfessionalsPage.tsx  # listagem profissionais + modal
│   └── ClinicalUsersPage.tsx  # listagem read-only usuários
```

### 3.2 Sidebar — atualizar `App.tsx`

```tsx
{ label: 'Grupos',        icon: IconUsersGroup,  path: '/groups'       },
{ label: 'Profissionais', icon: IconStethoscope, path: '/professionals' },
{ label: 'Equipe',        icon: IconUsers,       path: '/clinical-users'},
```

### 3.3 GroupsPage.tsx

```
┌──────────────────────────────────────────────┐
│ Grupos de Profissionais      [+ Criar Grupo] │
├──────────────────┬───────────┬───────────────┤
│ Nome             │ Unidade   │ Membros│Status │
├──────────────────┼───────────┼────────┼───────┤
│ ESF Centro       │ UBS Centro│   8    │● ativo│
│ Saúde Mental     │ Hosp. Alfa│   4    │● ativo│
└──────────────────┴───────────┴────────┴───────┘
```

### 3.4 ProfessionalsPage.tsx

```
┌────────────────────────────────────────────────────┐
│ Profissionais de Saúde        [+ Adicionar]        │
├──────────────┬────────┬──────────┬─────────────────┤
│ Nome         │ Conselho│Especialid│ Unidade│Status  │
├──────────────┼────────┼──────────┼────────┼────────┤
│ Dr. Silva    │ CRM    │ Clínica G│ UBS Ctr│● ativo │
│ Enf. Maria   │ COREN  │ Saúde Fam│ UBS Ctr│● ativo │
└──────────────┴────────┴──────────┴────────┴────────┘
```

### 3.5 Dashboard — atualizar `Dashboard.tsx`

Adicionar cards:
```
┌──────────────────────────────────┐
│ 👥 Equipe                        │
│ 12 profissionais ativos          │
│ 3 grupos                         │
└──────────────────────────────────┘
```

---

## 4. Dependência com DEM-031

`professional_groups` e `unit_professionals` referenciam `units` (criada no DEM-031). Portanto:

- **DEM-031 deve ser executado antes do DEM-032** (ou as migrations devem ser aplicadas em ordem: 005 → 006)
- Se DEM-031 ainda não estiver completo, aplicar pelo menos a criação da tabela `units` antes de rodar `006_clinico_gestao.sql`

---

## 5. Sequência de execução

```bash
# 1. Garantir que migration 005 (DEM-031) foi aplicada antes
# 2. Aplicar migration 006
docker exec -i intellicare-postgres psql -U intellicare intellicare \
  -c "SET search_path = tenant_alfa;" \
  < db/tenant_migrations/006_clinico_gestao.sql

# 3. Backend (schemas → service → router) + rebuild
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  build intellicare-service

# 4. Frontend (hooks → pages → App.tsx sidebar) + build
cd frontend/ClinicoUI && npx vite build

# 5. Restart
docker compose --env-file infra/.env -f infra/docker-compose.yml \
  restart intellicare-service
```

---

## 6. Checklist de entrega

- [ ] Migration `006_clinico_gestao.sql` aplicada (após 005)
- [ ] Endpoints de Grupos funcionando (CRUD + membros)
- [ ] Endpoints de Profissionais funcionando (CRUD)
- [ ] Endpoint `/cuidado/clinical-users` retornando lista
- [ ] ClinicoUI: 3 novas páginas na sidebar
- [ ] Dashboard com card de Equipe
- [ ] Build sem erros
- [ ] Commit: `feat(DEM-032): clinico gestao - grupos, profissionais, equipe`
