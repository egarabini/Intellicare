---
dem: DEM-013
titulo: Cuidado Backend — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-013 · 02 — Especificação Técnica

## Estrutura

```
modules/cuidado/
├── __init__.py
├── main.py
├── router.py
├── schemas.py
└── service.py

db/tenant_migrations/
└── 004_cuidado_tables.sql
```

## BLOCO 1 — `db/tenant_migrations/004_cuidado_tables.sql`

```sql
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    cpf TEXT UNIQUE,
    birth_date DATE,
    sex CHAR(1) CHECK (sex IN ('M','F','O')),
    phone TEXT, email TEXT, address TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    clinician_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
    chief_complaint TEXT,
    priority TEXT NOT NULL DEFAULT 'normal'
              CHECK (priority IN ('emergency','urgent','normal','low')),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS encounter_notes (
    id BIGSERIAL PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(id),
    clinician_id TEXT NOT NULL,
    subjective TEXT, objective TEXT, assessment TEXT, plan TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters (patient_id, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_encounter    ON encounter_notes (encounter_id, created_at);
CREATE INDEX IF NOT EXISTS idx_patients_name      ON patients USING gin (to_tsvector('portuguese', full_name));
```

## BLOCO 2 — `modules/cuidado/schemas.py`

```python
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

class PatientCreate(BaseModel):
    full_name: str
    cpf: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[Literal["M","F","O"]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class PatientResponse(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; active: bool; created_at: datetime

class EncounterCreate(BaseModel):
    patient_id: UUID
    chief_complaint: Optional[str] = None
    priority: Literal["emergency","urgent","normal","low"] = "normal"

class EncounterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; patient_id: UUID; clinician_id: str
    status: str; chief_complaint: Optional[str]; priority: str
    opened_at: datetime; closed_at: Optional[datetime]

class NoteCreate(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None

class NoteResponse(NoteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int; encounter_id: UUID; clinician_id: str; created_at: datetime

class ClinicalAskRequest(BaseModel):
    query: str
    limit: int = 5
    min_similarity: float = 0.5
```

## BLOCO 3 — `modules/cuidado/service.py`

```python
from sqlalchemy import text
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session
from uuid import UUID
import logging

logger = logging.getLogger("intellicare.cuidado")

class CuidadoService:

    async def create_patient(self, ctx, data):
        async with tenant_session(ctx) as db:
            row = (await db.execute(text(
                "INSERT INTO patients (full_name,cpf,birth_date,sex,phone,email,address) "
                "VALUES (:full_name,:cpf,:birth_date,:sex,:phone,:email,:address) RETURNING *"), data
            )).mappings().first()
        return dict(row)

    async def search_patients(self, ctx, q, limit=20):
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text(
                "SELECT * FROM patients WHERE active=true "
                "AND to_tsvector('portuguese',full_name) @@ plainto_tsquery('portuguese',:q) "
                "ORDER BY full_name LIMIT :lim"), {"q": q or " ", "lim": limit}
            )).mappings().all()
        return [dict(r) for r in rows]

    async def open_encounter(self, ctx, clinician_id, data):
        async with tenant_session(ctx) as db:
            row = (await db.execute(text(
                "INSERT INTO encounters (patient_id,clinician_id,chief_complaint,priority) "
                "VALUES (:patient_id,:clinician_id,:chief_complaint,:priority) RETURNING *"),
                {"clinician_id": clinician_id, **data}
            )).mappings().first()
        return dict(row)

    async def add_note(self, ctx, encounter_id: UUID, clinician_id, data):
        async with tenant_session(ctx) as db:
            enc = (await db.execute(text(
                "SELECT status FROM encounters WHERE id=:id"), {"id": str(encounter_id)})
            ).first()
            if not enc or enc[0] != "open":
                raise ValueError("Consulta não encontrada ou já encerrada")
            row = (await db.execute(text(
                "INSERT INTO encounter_notes (encounter_id,clinician_id,subjective,objective,assessment,plan) "
                "VALUES (:eid,:cid,:subjective,:objective,:assessment,:plan) RETURNING *"),
                {"eid": str(encounter_id), "cid": clinician_id, **data}
            )).mappings().first()
        return dict(row)

    async def close_encounter(self, ctx, encounter_id: UUID):
        async with tenant_session(ctx) as db:
            row = (await db.execute(text(
                "UPDATE encounters SET status='closed',closed_at=now() "
                "WHERE id=:id AND status='open' RETURNING *"), {"id": str(encounter_id)}
            )).mappings().first()
            if not row: raise LookupError("Consulta não encontrada ou já encerrada")
        return dict(row)

    async def patient_history(self, ctx, patient_id: UUID):
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text(
                "SELECT * FROM encounters WHERE patient_id=:pid ORDER BY opened_at DESC"),
                {"pid": str(patient_id)}
            )).mappings().all()
        return [dict(r) for r in rows]
```

## BLOCO 4 — `modules/cuidado/router.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from modules.slm.service import SLMService
from .schemas import ClinicalAskRequest, EncounterCreate, NoteCreate, PatientCreate
from .service import CuidadoService
from typing import Annotated
from uuid import UUID

router = APIRouter(prefix="/cuidado", tags=["cuidado"])
_svc = CuidadoService(); _slm = SLMService()
Clinico = Annotated[TenantContext, Depends(require_role("CLINICO"))]

@router.get("/health")
async def health(): return {"status":"healthy","module":"cuidado","version":"1.0.0"}

@router.post("/patients", status_code=201)
async def create_patient(p: PatientCreate, ctx: Clinico):
    return await _svc.create_patient(ctx, p.model_dump())

@router.get("/patients")
async def search_patients(q: str = "", ctx: Clinico = Depends(require_role("CLINICO"))):
    return await _svc.search_patients(ctx, q)

@router.get("/patients/{pid}/history")
async def history(pid: UUID, ctx: Clinico): return await _svc.patient_history(ctx, pid)

@router.post("/encounters", status_code=201)
async def open_encounter(e: EncounterCreate, ctx: Clinico):
    return await _svc.open_encounter(ctx, ctx.user_id, e.model_dump())

@router.post("/encounters/{eid}/notes", status_code=201)
async def add_note(eid: UUID, n: NoteCreate, ctx: Clinico):
    try: return await _svc.add_note(ctx, eid, ctx.user_id, n.model_dump())
    except ValueError as e: raise HTTPException(400, str(e))

@router.post("/encounters/{eid}/close")
async def close_encounter(eid: UUID, ctx: Clinico):
    try: return await _svc.close_encounter(ctx, eid)
    except LookupError as e: raise HTTPException(404, str(e))

@router.post("/encounters/{eid}/ask")
async def clinical_ask(eid: UUID, req: ClinicalAskRequest, ctx: Clinico):
    try: return await _slm.ask(req.query, ctx, req.limit, req.min_similarity)
    except (ConnectionError, RuntimeError) as e: raise HTTPException(503, str(e))
```

## BLOCO 5 — Commit

```bash
git add modules/cuidado/ db/tenant_migrations/004_cuidado_tables.sql docs/demandas/DEM-013_CUIDADO_BACKEND/
git commit -m "DEM-013: Cuidado Backend - pacientes, consultas SOAP, suporte SLM clinico"
git push origin main
```
