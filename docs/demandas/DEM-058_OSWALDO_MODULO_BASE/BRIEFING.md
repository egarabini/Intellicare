# DEM-058 — Oswaldo: Módulo Base (Assistente de Prescrição e CID-10)

> **Dev:** DEV-1
> **Estimativa:** ~4h
> **Dependência:** DEM-032 (ClinicoUI base), DEM-020 (EncounterView)
> **Executor Matrix:** `oswaldo_suggest_cid()` → **Hybrid** | `oswaldo_save_prescription()` → **Agent**

---

## Contexto

Oswaldo é o segundo módulo do Clinical Squad do IntelliCare. Enquanto Florence cuida
das notas SOAP, Oswaldo foca em dois problemas práticos do clínico no momento do
encontro:

1. **CID-10 sugerido** — busca e sugestão de código CID-10 com base na hipótese diagnóstica
2. **Prescrição estruturada** — registro de medicamentos, posologia e duração no encontro

Esta DEM entrega a **base do módulo** — estrutura, endpoints e UI — sem integração LLM
(isso vem em DEM-059+). O CID-10 nesta DEM é resolvido por busca textual na tabela
da CID-10 já existente no IntelliCare (DEM-020 já usa CID-10).

---

## Fase A — Backend

### STEP-001 — Migration

`migrations/014_oswaldo_prescriptions.sql`:

```sql
CREATE TABLE IF NOT EXISTS prescriptions (
    id              BIGSERIAL PRIMARY KEY,
    encounter_id    BIGINT NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    patient_id      BIGINT NOT NULL,
    author_id       UUID NOT NULL,
    author_name     TEXT NOT NULL,
    cid10_code      TEXT,                    -- ex: "J00", "K21.0"
    cid10_desc      TEXT,                    -- ex: "Rinofaringite aguda"
    items           JSONB NOT NULL DEFAULT '[]',
    -- item: {"drug": "Ibuprofeno 600mg", "posology": "1 comp 8/8h", "duration": "5 dias"}
    notes           TEXT,
    status          TEXT NOT NULL DEFAULT 'DRAFT',  -- DRAFT | SIGNED
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_prescriptions_encounter ON prescriptions(encounter_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient   ON prescriptions(patient_id);
```

### STEP-002 — Contracts

`modules/oswaldo/contracts.py`:

```python
from pydantic import BaseModel
from datetime import datetime

class PrescriptionItem(BaseModel):
    drug: str
    posology: str
    duration: str | None = None
    notes: str | None = None

class CreatePrescriptionRequest(BaseModel):
    encounter_id: int
    patient_id: int
    cid10_code: str | None = None
    cid10_desc: str | None = None
    items: list[PrescriptionItem] = []
    notes: str | None = None

class Prescription(BaseModel):
    id: int
    encounter_id: int
    patient_id: int
    author_id: str
    author_name: str
    cid10_code: str | None
    cid10_desc: str | None
    items: list[PrescriptionItem]
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime

class CID10Result(BaseModel):
    code: str
    description: str
```

### STEP-003 — Repository

`modules/oswaldo/repository.py`:

```python
async def create_prescription(
    ctx: TenantContext,
    req: CreatePrescriptionRequest,
    author_id: str,
    author_name: str,
) -> Prescription:
    import json
    row = await ctx.db.fetchrow(
        """
        INSERT INTO prescriptions
          (encounter_id, patient_id, author_id, author_name,
           cid10_code, cid10_desc, items, notes)
        VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8)
        RETURNING *
        """,
        req.encounter_id, req.patient_id, author_id, author_name,
        req.cid10_code, req.cid10_desc,
        json.dumps([i.model_dump() for i in req.items]),
        req.notes,
    )
    return _row_to_prescription(row)

async def get_prescriptions_by_encounter(
    ctx: TenantContext, encounter_id: int
) -> list[Prescription]:
    rows = await ctx.db.fetch(
        "SELECT * FROM prescriptions WHERE encounter_id = $1 ORDER BY created_at ASC",
        encounter_id,
    )
    return [_row_to_prescription(r) for r in rows]

async def search_cid10(ctx: TenantContext, query: str) -> list[CID10Result]:
    """Busca textual na tabela cid10 existente (DEM-020)."""
    rows = await ctx.db.fetch(
        """
        SELECT code, description FROM cid10
        WHERE description ILIKE $1 OR code ILIKE $1
        ORDER BY code LIMIT 10
        """,
        f"%{query}%",
    )
    return [CID10Result(code=r["code"], description=r["description"]) for r in rows]
```

### STEP-004 — Routes

`modules/oswaldo/api/routes.py`:

```python
router = APIRouter(prefix="/oswaldo", tags=["oswaldo"])

@router.get("/cid10/search", response_model=list[CID10Result])
async def search_cid10(
    q: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _: UserClaims = Depends(require_roles(["CLINICO"])),
):
    if len(q) < 2:
        return []
    return await repo.search_cid10(ctx, q)

@router.post("/prescriptions", response_model=Prescription)
async def create_prescription(
    req: CreatePrescriptionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    user: UserClaims = Depends(require_roles(["CLINICO"])),
):
    return await repo.create_prescription(ctx, req, user.sub, user.name)

@router.get("/prescriptions/encounter/{encounter_id}", response_model=list[Prescription])
async def list_prescriptions(
    encounter_id: int,
    ctx: TenantContext = Depends(get_tenant_context),
    _: UserClaims = Depends(require_roles(["CLINICO", "GESTOR"])),
):
    return await repo.get_prescriptions_by_encounter(ctx, encounter_id)
```

### STEP-005 — Registro do módulo

Incluir o router `oswaldo` no loader de módulos seguindo o padrão de `florence`
(ver `docs/patterns/backend-modules.md`).

---

## Fase B — Frontend ClinicoUI

### STEP-006 — OswaldoCID10Search component

`ClinicoUI/components/OswaldoCID10Search.tsx`:

```tsx
// Autocomplete com debounce de 300ms
// Ao selecionar: preenche cid10_code e cid10_desc no formulário pai
<Autocomplete
  label="CID-10"
  placeholder="Digite diagnóstico ou código (ex: J00)"
  data={results.map(r => ({ value: r.code, label: `${r.code} — ${r.description}` }))}
  onChange={debounce(handleSearch, 300)}
  onOptionSubmit={(code) => onSelect(results.find(r => r.code === code))}
/>
```

### STEP-007 — OswaldoPrescriptionEditor component

`ClinicoUI/components/OswaldoPrescriptionEditor.tsx`:

```tsx
// Lista de itens (drug + posology + duration)
// Botão "+ Adicionar medicamento"
// Botão "Salvar prescrição"
// Exibe prescrições salvas em cards com status DRAFT/SIGNED
```

### STEP-008 — Aba "Oswaldo" em EncounterView

`ClinicoUI/pages/EncounterView.tsx` — adicionar aba junto à aba Florence:

```tsx
<Tabs.Tab value="oswaldo" leftSection={<IconPill size={14} />}>
  Prescrição
</Tabs.Tab>

<Tabs.Panel value="oswaldo">
  <OswaldoCID10Search onSelect={setCID10} />
  <OswaldoPrescriptionEditor encounterId={encounterId} patientId={patientId} cid10={cid10} />
</Tabs.Panel>
```

---

## Fase C — Testes

### STEP-009 — Testes Python

`packages/intellicare-core/tests/test_oswaldo.py`:

```python
async def test_create_prescription(async_client):
    resp = await async_client.post("/oswaldo/prescriptions", json={
        "encounter_id": 1,
        "patient_id": 1,
        "cid10_code": "J00",
        "cid10_desc": "Rinofaringite aguda",
        "items": [
            {"drug": "Ibuprofeno 600mg", "posology": "1 comp 8/8h", "duration": "5 dias"}
        ],
    })
    assert resp.status_code == 200
    assert resp.json()["cid10_code"] == "J00"
    assert len(resp.json()["items"]) == 1

async def test_search_cid10(async_client):
    resp = await async_client.get("/oswaldo/cid10/search?q=rinofar")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

async def test_list_prescriptions_by_encounter(async_client):
    resp = await async_client.get("/oswaldo/prescriptions/encounter/1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

---

## Critérios de Aceite

- [ ] Migration 014 aplicada sem erro
- [ ] `GET /oswaldo/cid10/search?q=` retorna lista de CID-10 filtrada
- [ ] `POST /oswaldo/prescriptions` cria prescrição com itens JSONB
- [ ] `GET /oswaldo/prescriptions/encounter/{id}` lista prescrições
- [ ] `OswaldoCID10Search` com autocomplete na aba ClinicoUI
- [ ] `OswaldoPrescriptionEditor` com lista de itens e salvar
- [ ] Aba "Prescrição" visível em `EncounterView`
- [ ] 3 testes passando

---

## Executor Matrix

| Componente | Categoria | Justificativa |
|---|---|---|
| `repo.search_cid10()` | Worker | Somente leitura, sem efeito externo |
| `repo.create_prescription()` | Agent | Persiste dado clínico com consequência legal — requer autor autenticado |
| `OswaldoCID10Search` | Worker | UI de busca, sem side effect |
| `OswaldoPrescriptionEditor` | Hybrid | Clínico preenche e decide salvar — não auto-salva |
