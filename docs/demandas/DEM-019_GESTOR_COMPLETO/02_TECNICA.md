# DEM-019 — Gestor Módulo Completo — Especificação Técnica

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + SQLAlchemy (async) + asyncpg |
| Frontend | React 18 + Vite + Mantine UI 7 + @mantine/dropzone |
| Auth | Keycloak OIDC — role `TENANT_GESTOR` |
| DB | PostgreSQL schema `tenant_{slug}` |
| Realtime | SSE (Server-Sent Events) para progresso RAG |
| Build estático | `npm run build` → `static/gestor-ui/` |

---

## 1. Backend — Novos Endpoints

> Todos os endpoints herdam `tenant_ctx: TenantContext = Depends(require_gestor)`
> O módulo gestor **não deve ter prefixo local** — o ModuleLoader aplica `/gestor`.

### 1.1 Dashboard

```
GET /gestor/dashboard/stats
```

**Response 200:**
```json
{
  "patients_active": 142,
  "appointments_today": 8,
  "appointments_week": 31,
  "appointments_month": 104,
  "invoices_pending_count": 12,
  "invoices_pending_total": 4850.00,
  "rag_documents_count": 23,
  "recent_activity": [
    {"timestamp": "2026-03-14T10:22:00Z", "action": "patient.created", "user": "dr.silva", "detail": "Paciente João..."}
  ]
}
```

**SQL (schema dinâmico):**
```sql
SET search_path TO tenant_{slug};
SELECT COUNT(*) FILTER (WHERE active) AS patients_active FROM patients;
SELECT COUNT(*) FROM appointments WHERE date_trunc('day', scheduled_at) = CURRENT_DATE;
SELECT COUNT(*) FROM appointments WHERE scheduled_at >= date_trunc('week', NOW());
SELECT COUNT(*) FROM appointments WHERE scheduled_at >= date_trunc('month', NOW());
SELECT COUNT(*), COALESCE(SUM(amount),0) FROM invoices WHERE status = 'pending';
SELECT COUNT(*) FROM rag_documents WHERE status = 'indexed';
SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 5;
```

---

### 1.2 Pacientes

```
GET    /gestor/patients?page=1&size=20&q=joao
POST   /gestor/patients
GET    /gestor/patients/{patient_id}
PATCH  /gestor/patients/{patient_id}
DELETE /gestor/patients/{patient_id}   # soft delete (active=false)
```

**Schema de criação (`POST /gestor/patients`):**
```json
{
  "name": "string (required)",
  "cpf": "string (11 dígitos, required)",
  "birth_date": "date (required)",
  "email": "string (optional)",
  "phone": "string (optional)",
  "health_plan": "string (optional)"
}
```

**Validações:**
- CPF: 11 dígitos numéricos, algoritmo de dígito verificador
- `UNIQUE(cpf)` por tenant — retorna HTTP 409 com `{"detail": "CPF já cadastrado"}`

**Migration SQL:**
```sql
CREATE TABLE IF NOT EXISTS patients (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    cpf         CHAR(11) NOT NULL,
    birth_date  DATE NOT NULL,
    email       TEXT,
    phone       TEXT,
    health_plan TEXT,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(cpf)
);
CREATE INDEX IF NOT EXISTS patients_name_idx ON patients USING gin(to_tsvector('portuguese', name));
```

---

### 1.3 Agendamentos

```
GET    /gestor/appointments?date=2026-03-14&clinician_id=uuid
POST   /gestor/appointments
PATCH  /gestor/appointments/{appt_id}
DELETE /gestor/appointments/{appt_id}   # cancela (status='cancelled')
```

**Schema de criação:**
```json
{
  "patient_id": "uuid",
  "clinician_id": "uuid (keycloak user_id do clínico)",
  "scheduled_at": "datetime ISO8601",
  "type": "consulta|retorno|exame",
  "notes": "string (optional)"
}
```

**Validação de conflito:**
```sql
SELECT id FROM appointments
WHERE clinician_id = :clinician_id
  AND status NOT IN ('cancelled')
  AND scheduled_at BETWEEN :start AND :end;
```
Se retornar linha → HTTP 409 `{"detail": "Clínico já tem agendamento neste horário"}`

**Migration SQL:**
```sql
CREATE TABLE IF NOT EXISTS appointments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id   UUID NOT NULL REFERENCES patients(id),
    clinician_id UUID NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    type         TEXT NOT NULL CHECK (type IN ('consulta','retorno','exame')),
    status       TEXT NOT NULL DEFAULT 'agendado'
                      CHECK (status IN ('agendado','confirmado','realizado','cancelado')),
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS appt_clinician_date ON appointments(clinician_id, scheduled_at);
```

---

### 1.4 Faturas (extensão do módulo financeiro)

```
GET  /gestor/invoices?page=1&size=20&status=pending&from=2026-01-01&to=2026-03-31
GET  /gestor/invoices/export-csv
PATCH /gestor/invoices/{invoice_id}/mark-paid
```

**CSV export** — usa `io.StringIO` + `csv.DictWriter`, header `Content-Disposition: attachment; filename=faturas.csv`.

**Response /export-csv:** `text/csv`

---

### 1.5 Documentos RAG

```
POST   /gestor/rag/upload          # multipart/form-data
GET    /gestor/rag/documents
DELETE /gestor/rag/documents/{doc_id}
GET    /gestor/rag/progress/{doc_id}  # SSE stream
```

**Upload flow:**
1. Salva arquivo em `/tmp/{tenant_slug}/{uuid}.{ext}`
2. Insere registro em `rag_documents` com `status='processing'`
3. Dispara task em background (`BackgroundTasks`) → chama `RAGModule.index_document()`
4. Atualiza `status='indexed'` ou `status='error'` ao final

**SSE `/gestor/rag/progress/{doc_id}`:**
```python
async def rag_progress_stream(doc_id: str, tenant_ctx, db):
    while True:
        doc = await db.get(RagDocument, doc_id)
        yield f"data: {doc.status}\n\n"
        if doc.status in ("indexed", "error"):
            break
        await asyncio.sleep(1)
```

---

### 1.6 Equipe Clínica

```
GET   /gestor/clinicians
POST  /gestor/clinicians/invite        # envia e-mail via Keycloak Admin API
PATCH /gestor/clinicians/{user_id}/deactivate
```

**Invite flow** (igual ao DEM-018 para usuários admin, mas com role `CLINICO`):
```python
async def invite_clinician(email: str, tenant_ctx, keycloak_admin):
    user = await keycloak_admin.create_user(email=email, realm="intellicare")
    await keycloak_admin.assign_role(user["id"], "CLINICO")
    await keycloak_admin.add_to_group(user["id"], f"tenant_{tenant_ctx.slug}")
    await keycloak_admin.send_verify_email(user["id"])
```

---

### 1.7 Programas de Saúde (extensão do DEM-011/014)

```
GET   /gestor/programs
POST  /gestor/programs
PATCH /gestor/programs/{program_id}
GET   /gestor/programs/{program_id}/patients
POST  /gestor/programs/{program_id}/patients/{patient_id}/enroll
DELETE /gestor/programs/{program_id}/patients/{patient_id}
GET   /gestor/programs/{program_id}/coverage-report
```

**Coverage report response:**
```json
{
  "program_id": "uuid",
  "program_name": "HiperDia",
  "eligible_patients": 80,
  "enrolled_patients": 62,
  "coverage_pct": 77.5,
  "overdue_patients": 8
}
```

---

### 1.8 Configurações do Tenant

```
GET   /gestor/tenant/settings
PATCH /gestor/tenant/settings
```

**Schema PATCH:**
```json
{
  "display_name": "Clínica São Lucas",
  "cnpj": "00.000.000/0001-00",
  "phone": "(11) 9999-9999",
  "address": "Rua X, 100 — São Paulo/SP",
  "logo_url": "https://..."
}
```

---

## 2. Frontend — GestorUI

> Localização: `frontend/GestorUI/src/`
> Stack: React 18 + Vite + Mantine 7 + React Router 6
> Build: `npm run build` → `packages/intellicare-core/intellicare_core/static/gestor-ui/`
> Dev: porta `5175`
> client_id Keycloak: `gestor-ui`

### 2.1 Estrutura de Rotas

```
/                    → redirect para /dashboard
/dashboard           → Dashboard.tsx
/patients            → PatientList.tsx
/patients/:id        → PatientProfile.tsx
/appointments        → AppointmentCalendar.tsx
/financeiro          → InvoiceList.tsx
/rag                 → RagDocuments.tsx
/programas           → ProgramList.tsx
/programas/:id       → ProgramDetail.tsx
/equipe              → ClinicianList.tsx
/settings            → TenantSettings.tsx
```

### 2.2 Componentes Principais

**`Dashboard.tsx`**
```tsx
// KPI cards usando Mantine <Card> + <Grid>
// 6 cards: Pacientes | Consultas Hoje | Semana | Mês | Faturas Pendentes | Docs RAG
// Auto-refresh: useEffect + setInterval(60_000)
// ActivityFeed: lista dos últimos 5 eventos do audit_log
```

**`PatientList.tsx`**
```tsx
// <TextInput> busca com debounce 300ms
// <Table> paginada (Mantine Pagination)
// Botão "Novo Paciente" → abre <Modal> com formulário validado por Zod
// Ação "Desativar" → confirm dialog → PATCH active=false
```

**`AppointmentCalendar.tsx`**
```tsx
// Usa @mantine/dates Calendar (mensal) + lista lateral (diária)
// Filtro por clínico (<Select>)
// Click em slot vazio → abre modal "Novo Agendamento"
// Click em evento → abre modal "Detalhes / Editar / Cancelar"
```

**`RagDocuments.tsx`**
```tsx
// @mantine/dropzone para upload (accept: pdf, docx, txt, md; maxSize: 50MB)
// Lista de documentos com badge de status (processando/indexado/erro)
// SSE hook: useEffect → new EventSource('/gestor/rag/progress/{id}')
// Barra de progresso enquanto status='processing'
```

**`InvoiceList.tsx`**
```tsx
// Filtros: DateRangePicker (from/to) + Select status
// Tabela com colunas: Paciente | Data | Valor | Status | Ações
// Botão "Marcar Pago" → PATCH /gestor/invoices/{id}/mark-paid
// Botão "Exportar CSV" → GET /gestor/invoices/export-csv → download automático
//   window.open('/gestor/invoices/export-csv?...')
```

**`ClinicianList.tsx`**
```tsx
// Lista de clínicos do tenant
// Botão "Convidar Clínico" → modal com e-mail input
// Botão "Desativar" → confirm → PATCH /gestor/clinicians/{id}/deactivate
```

**`TenantSettings.tsx`**
```tsx
// Formulário com campos: nome, CNPJ, telefone, endereço, logo URL
// GET /gestor/tenant/settings → preenche form
// Submit → PATCH /gestor/tenant/settings
// Seção "Uso" (read-only): pacientes cadastrados / limite, clínicos / limite, storage RAG
```

---

## 3. Autenticação no Frontend

Mesmo padrão das outras UIs — OIDC em memória, sem localStorage:

```tsx
// src/auth/AuthProvider.tsx
const oidcConfig = {
  authority: import.meta.env.VITE_KEYCLOAK_URL + '/realms/intellicare',
  client_id: 'gestor-ui',
  redirect_uri: window.location.origin + '/callback',
  scope: 'openid profile email',
  response_type: 'code',
};
```

Proteção de rota — verificar role `TENANT_GESTOR` no token:
```tsx
const roles = user?.profile?.realm_access?.roles ?? [];
if (!roles.includes('TENANT_GESTOR')) navigate('/unauthorized');
```

---

## 4. Migrations

Arquivo: `packages/intellicare-core/intellicare_core/modules/gestor/migrations.py`

```python
GESTOR_MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS patients (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        cpf CHAR(11) NOT NULL,
        birth_date DATE NOT NULL,
        email TEXT,
        phone TEXT,
        health_plan TEXT,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(cpf)
    );
    CREATE INDEX IF NOT EXISTS patients_name_idx
        ON patients USING gin(to_tsvector('portuguese', name));
    """,
    """
    CREATE TABLE IF NOT EXISTS appointments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        patient_id UUID NOT NULL REFERENCES patients(id),
        clinician_id UUID NOT NULL,
        scheduled_at TIMESTAMPTZ NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('consulta','retorno','exame')),
        status TEXT NOT NULL DEFAULT 'agendado'
            CHECK (status IN ('agendado','confirmado','realizado','cancelado')),
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS appt_clinician_date
        ON appointments(clinician_id, scheduled_at);
    """,
]
```

Chamar em `GestorModule.startup()`:
```python
async def startup(self):
    async with get_db() as db:
        for sql in GESTOR_MIGRATIONS:
            await db.execute(text(sql))
```

---

## 5. Testes

Arquivo: `packages/intellicare-core/tests/test_gestor.py`

```python
@pytest.mark.asyncio
async def test_dashboard_stats(client, gestor_token, seed_tenant):
    r = await client.get("/gestor/dashboard/stats",
                         headers={"Authorization": f"Bearer {gestor_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "patients_active" in data
    assert "appointments_today" in data

@pytest.mark.asyncio
async def test_create_patient_cpf_duplicate(client, gestor_token):
    payload = {"name": "Ana", "cpf": "12345678901", "birth_date": "1990-01-01"}
    await client.post("/gestor/patients", json=payload,
                      headers={"Authorization": f"Bearer {gestor_token}"})
    r = await client.post("/gestor/patients", json=payload,
                          headers={"Authorization": f"Bearer {gestor_token}"})
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_appointment_conflict(client, gestor_token, seed_patient, seed_clinician):
    slot = {"patient_id": seed_patient, "clinician_id": seed_clinician,
            "scheduled_at": "2026-04-01T09:00:00Z", "type": "consulta"}
    await client.post("/gestor/appointments", json=slot,
                      headers={"Authorization": f"Bearer {gestor_token}"})
    r = await client.post("/gestor/appointments", json=slot,
                          headers={"Authorization": f"Bearer {gestor_token}"})
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_tenant_isolation(client, gestor_token_tenant_b):
    r = await client.get("/gestor/patients",
                         headers={"Authorization": f"Bearer {gestor_token_tenant_b}"})
    # deve retornar lista vazia do tenant B, não pacientes do tenant A
    assert r.status_code == 200
    assert r.json()["items"] == []
```

---

## 6. Checklist de Entrega

- [ ] Migrations executadas em todos os tenants do seed
- [ ] Todos os endpoints respondem com TenantContext isolado
- [ ] Frontend builda sem erros (`npm run build`)
- [ ] Build copiado para `static/gestor-ui/`
- [ ] SSE de progresso RAG funciona (testar com arquivo > 1MB)
- [ ] Export CSV abre download no browser
- [ ] Testes passam: `pytest tests/test_gestor.py -v`
- [ ] Commit com mensagem: `feat(DEM-019): gestor modulo completo`
