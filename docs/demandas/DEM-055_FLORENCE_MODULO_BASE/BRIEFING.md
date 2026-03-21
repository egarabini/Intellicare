# DEM-055 — Florence: Módulo Base (Assistente de Notas Clínicas)

> **Dev:** DEV-2
> **Estimativa:** ~4h
> **Dependência:** DEM-032 (ClinicoUI base), DEM-020 (EncounterView)

---

## Contexto

Florence é o módulo de assistência à documentação clínica do IntelliCare. O objetivo
desta DEM é criar a **base do módulo** — estrutura de dados, endpoints e tela no
ClinicoUI — sem ainda integrar modelos de IA (essa integração vem em DEM-056+).

O fluxo do clínico hoje é: ver agenda → abrir encontro → escrever anotação livre.
Florence adiciona uma estrutura SOAP opcional: Subjetivo, Objetivo, Avaliação, Plano.
O clínico pode preencher os campos estruturados, ou ignorá-los e seguir com texto livre.

---

## Fase A — Backend

### STEP-001 — Migration

`migrations/013_florence_notes.sql`:

```sql
CREATE TABLE IF NOT EXISTS clinical_notes (
    id          BIGSERIAL PRIMARY KEY,
    encounter_id BIGINT NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    patient_id  BIGINT NOT NULL,
    author_id   UUID NOT NULL,              -- sub do Keycloak
    author_name TEXT NOT NULL,
    note_type   TEXT NOT NULL DEFAULT 'FREE', -- FREE | SOAP
    -- campos SOAP (todos opcionais)
    soap_s      TEXT,                        -- Subjetivo
    soap_o      TEXT,                        -- Objetivo
    soap_a      TEXT,                        -- Avaliação
    soap_p      TEXT,                        -- Plano
    -- campo livre (sempre presente como fallback)
    free_text   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clinical_notes_encounter ON clinical_notes(encounter_id);
CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient   ON clinical_notes(patient_id);
```

### STEP-002 — Contracts

`modules/florence/contracts.py`:

```python
from enum import StrEnum
from pydantic import BaseModel
from datetime import datetime

class NoteType(StrEnum):
    FREE = "FREE"
    SOAP = "SOAP"

class CreateNoteRequest(BaseModel):
    encounter_id: int
    patient_id: int
    note_type: NoteType = NoteType.FREE
    soap_s: str | None = None
    soap_o: str | None = None
    soap_a: str | None = None
    soap_p: str | None = None
    free_text: str | None = None

class ClinicalNote(BaseModel):
    id: int
    encounter_id: int
    patient_id: int
    author_id: str
    author_name: str
    note_type: NoteType
    soap_s: str | None
    soap_o: str | None
    soap_a: str | None
    soap_p: str | None
    free_text: str | None
    created_at: datetime
    updated_at: datetime
```

### STEP-003 — Repository

`modules/florence/repository.py`:

```python
async def create_note(ctx: TenantContext, req: CreateNoteRequest, author_id: str, author_name: str) -> ClinicalNote:
    row = await ctx.db.fetchrow(
        """
        INSERT INTO clinical_notes
          (encounter_id, patient_id, author_id, author_name,
           note_type, soap_s, soap_o, soap_a, soap_p, free_text)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        RETURNING *
        """,
        req.encounter_id, req.patient_id, author_id, author_name,
        req.note_type, req.soap_s, req.soap_o, req.soap_a, req.soap_p, req.free_text,
    )
    return ClinicalNote(**row)

async def get_notes_by_encounter(ctx: TenantContext, encounter_id: int) -> list[ClinicalNote]:
    rows = await ctx.db.fetch(
        "SELECT * FROM clinical_notes WHERE encounter_id = $1 ORDER BY created_at ASC",
        encounter_id,
    )
    return [ClinicalNote(**r) for r in rows]

async def get_notes_by_patient(ctx: TenantContext, patient_id: int) -> list[ClinicalNote]:
    rows = await ctx.db.fetch(
        "SELECT * FROM clinical_notes WHERE patient_id = $1 ORDER BY created_at DESC LIMIT 50",
        patient_id,
    )
    return [ClinicalNote(**r) for r in rows]
```

### STEP-004 — Routes

`modules/florence/api/routes.py`:

```python
router = APIRouter(prefix="/florence", tags=["florence"])

@router.post("/notes", response_model=ClinicalNote)
async def create_note(
    req: CreateNoteRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    user: UserClaims = Depends(require_roles(["CLINICO"])),
):
    return await repo.create_note(ctx, req, user.sub, user.name)

@router.get("/notes/encounter/{encounter_id}", response_model=list[ClinicalNote])
async def list_notes_by_encounter(
    encounter_id: int,
    ctx: TenantContext = Depends(get_tenant_context),
    _: UserClaims = Depends(require_roles(["CLINICO", "GESTOR"])),
):
    return await repo.get_notes_by_encounter(ctx, encounter_id)

@router.get("/notes/patient/{patient_id}", response_model=list[ClinicalNote])
async def list_notes_by_patient(
    patient_id: int,
    ctx: TenantContext = Depends(get_tenant_context),
    _: UserClaims = Depends(require_roles(["CLINICO", "GESTOR"])),
):
    return await repo.get_notes_by_patient(ctx, patient_id)
```

### STEP-005 — Registro do módulo

Em `modules/__init__.py` (ou `app.py`), incluir o router florence seguindo o
padrão dos outros módulos (loader dinâmico ou include explícito — ver
`docs/patterns/backend-modules.md`).

---

## Fase B — Frontend ClinicoUI

### STEP-006 — FlorenceNoteEditor component

`ClinicoUI/components/FlorenceNoteEditor.tsx`:

```tsx
// Props
interface Props {
  encounterId: number
  patientId: number
  onSaved: () => void
}

// Estado
const [noteType, setNoteType] = useState<'FREE' | 'SOAP'>('FREE')
const [fields, setFields] = useState({ s: '', o: '', a: '', p: '', free: '' })

// UI
<SegmentedControl
  value={noteType}
  onChange={(v) => setNoteType(v as 'FREE' | 'SOAP')}
  data={[{ label: 'Texto livre', value: 'FREE' }, { label: 'SOAP', value: 'SOAP' }]}
/>

{noteType === 'SOAP' ? (
  <>
    <Textarea label="S — Subjetivo" ... />
    <Textarea label="O — Objetivo" ... />
    <Textarea label="A — Avaliação" ... />
    <Textarea label="P — Plano" ... />
  </>
) : (
  <Textarea label="Anotação" rows={6} ... />
)}

<Button onClick={handleSave}>Salvar nota</Button>
```

### STEP-007 — Integrar em EncounterView

Em `ClinicoUI/pages/EncounterView.tsx`, adicionar aba "Notas Florence":

```tsx
<Tabs.Tab value="florence" leftSection={<IconNotes size={14} />}>
  Notas
</Tabs.Tab>

<Tabs.Panel value="florence">
  <FlorenceNoteEditor encounterId={encounterId} patientId={patientId} onSaved={refetch} />
  <FlorenceNoteList notes={notes} />
</Tabs.Panel>
```

`FlorenceNoteList` exibe as notas existentes em cards ordenados por data, com
badge `SOAP` ou `LIVRE` e preview das primeiras 100 chars.

---

## Fase C — Testes

### STEP-008 — Testes Python

`packages/intellicare-core/tests/test_florence.py`:

```python
async def test_create_free_note(async_client):
    resp = await async_client.post("/florence/notes", json={
        "encounter_id": 1,
        "patient_id": 1,
        "note_type": "FREE",
        "free_text": "Paciente relata melhora.",
    })
    assert resp.status_code == 200
    assert resp.json()["note_type"] == "FREE"

async def test_create_soap_note(async_client):
    resp = await async_client.post("/florence/notes", json={
        "encounter_id": 1,
        "patient_id": 1,
        "note_type": "SOAP",
        "soap_s": "Dor de cabeça há 2 dias",
        "soap_o": "PA 120/80, FC 72bpm",
        "soap_a": "Cefaleia tensional provável",
        "soap_p": "Analgésico + repouso",
    })
    assert resp.status_code == 200
    assert resp.json()["soap_a"] == "Cefaleia tensional provável"

async def test_list_notes_by_encounter(async_client):
    resp = await async_client.get("/florence/notes/encounter/1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

---

## Critérios de Aceite

- [ ] Migration 013 aplicada sem erro
- [ ] `POST /florence/notes` cria nota FREE e SOAP
- [ ] `GET /florence/notes/encounter/{id}` lista notas do encontro
- [ ] `GET /florence/notes/patient/{id}` lista últimas 50 notas do paciente
- [ ] `FlorenceNoteEditor` exibe toggle FREE/SOAP no ClinicoUI
- [ ] Aba "Notas" visível em `EncounterView`
- [ ] 3 testes passando

---

## Nota Arquitetural

Florence é Camada 3 do IA-FRAMEWORK (Clinical Squad). Esta DEM entrega apenas a
**estrutura de dados e UI base** — sem IA. A próxima evolução (DEM-057+) pode
adicionar sugestão automática de preenchimento SOAP usando o modelo oswaldo ou
um endpoint de LLM interno. Manter os campos SOAP como texto simples facilita
essa futura integração: o LLM recebe o contexto do encontro e devolve sugestões
nos 4 campos.
