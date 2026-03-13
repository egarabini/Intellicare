# DEM-014 — Programas de Saúde: Especificação Técnica

## 1. Arquivos a Criar / Modificar

```
db/tenant_migrations/005_programas_tables.sql
modules/programas/__init__.py
modules/programas/schemas.py
modules/programas/service.py
modules/programas/router.py
modules/programas/main.py
tests/programas/test_programas_service.py
```

---

## 2. Migration SQL

**`db/tenant_migrations/005_programas_tables.sql`**

```sql
-- ============================================================
-- DEM-014: Programas de Saúde
-- Tenant schema: tenant_{slug}
-- ============================================================

CREATE TABLE IF NOT EXISTS health_programs (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    target_count INTEGER NOT NULL DEFAULT 0,   -- meta de pacientes
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_by  VARCHAR(100),                  -- user_id do gestor
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS program_enrollments (
    id          BIGSERIAL PRIMARY KEY,
    program_id  BIGINT NOT NULL REFERENCES health_programs(id) ON DELETE CASCADE,
    patient_id  BIGINT NOT NULL REFERENCES patients(id)        ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    enrolled_by VARCHAR(100),                  -- user_id do clinico/gestor
    status      VARCHAR(20)  NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active','discharged','suspended')),
    notes       TEXT,
    CONSTRAINT uq_enrollment UNIQUE (program_id, patient_id)
);

CREATE INDEX IF NOT EXISTS idx_enrollments_program ON program_enrollments(program_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_patient ON program_enrollments(patient_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status  ON program_enrollments(status);
```

---

## 3. Schemas Pydantic

**`modules/programas/schemas.py`**

```python
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Programas ────────────────────────────────────────────────

class ProgramCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    target_count: int = Field(default=0, ge=0)

class ProgramResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_count: int
    active: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Enrollments ──────────────────────────────────────────────

class EnrollRequest(BaseModel):
    patient_id: int
    notes: Optional[str] = None

class EnrollmentResponse(BaseModel):
    id: int
    program_id: int
    patient_id: int
    enrolled_at: datetime
    enrolled_by: Optional[str]
    status: str
    notes: Optional[str]

    model_config = {"from_attributes": True}


# ── Relatórios ───────────────────────────────────────────────

class OverduePatient(BaseModel):
    patient_id: int
    full_name: str
    last_encounter_date: Optional[datetime]
    days_without_visit: int

class CoverageReport(BaseModel):
    program_id: int
    program_name: str
    target_count: int
    enrolled_count: int
    coverage_pct: float           # enrolled / target * 100
    overdue_count: int            # sem visita há > threshold dias
```

---

## 4. Service

**`modules/programas/service.py`**

```python
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from intellicare_core.context import TenantContext
from modules.programas.schemas import (
    CoverageReport,
    EnrollRequest,
    EnrollmentResponse,
    OverduePatient,
    ProgramCreate,
    ProgramResponse,
)

logger = logging.getLogger(__name__)


class ProgramasService:
    """Gerencia programas de saúde e matrículas de pacientes."""

    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self._session = session
        self._ctx = ctx

    # ── Programas ────────────────────────────────────────────

    async def list_programs(self, active_only: bool = True) -> List[ProgramResponse]:
        where = "WHERE active = TRUE" if active_only else ""
        rows = await self._session.execute(
            text(f"""
                SELECT id, name, description, target_count, active,
                       created_by, created_at, updated_at
                FROM   health_programs
                {where}
                ORDER BY name
            """)
        )
        return [ProgramResponse.model_validate(dict(r._mapping)) for r in rows]

    async def create_program(self, data: ProgramCreate) -> ProgramResponse:
        row = await self._session.execute(
            text("""
                INSERT INTO health_programs (name, description, target_count, created_by)
                VALUES (:name, :description, :target_count, :created_by)
                RETURNING id, name, description, target_count, active,
                          created_by, created_at, updated_at
            """),
            {
                "name": data.name,
                "description": data.description,
                "target_count": data.target_count,
                "created_by": self._ctx.user_id,
            },
        )
        await self._session.commit()
        return ProgramResponse.model_validate(dict(row.one()._mapping))

    async def deactivate_program(self, program_id: int) -> None:
        await self._session.execute(
            text("UPDATE health_programs SET active=FALSE, updated_at=NOW() WHERE id=:id"),
            {"id": program_id},
        )
        await self._session.commit()

    # ── Matrículas ───────────────────────────────────────────

    async def enroll(self, program_id: int, req: EnrollRequest) -> EnrollmentResponse:
        """Matricula paciente; ignora duplicata (ON CONFLICT DO NOTHING)."""
        row = await self._session.execute(
            text("""
                INSERT INTO program_enrollments
                    (program_id, patient_id, enrolled_by, notes)
                VALUES
                    (:program_id, :patient_id, :enrolled_by, :notes)
                ON CONFLICT ON CONSTRAINT uq_enrollment DO UPDATE
                    SET status = 'active',
                        notes  = EXCLUDED.notes,
                        enrolled_at = NOW()
                RETURNING id, program_id, patient_id, enrolled_at,
                          enrolled_by, status, notes
            """),
            {
                "program_id": program_id,
                "patient_id": req.patient_id,
                "enrolled_by": self._ctx.user_id,
                "notes": req.notes,
            },
        )
        await self._session.commit()
        return EnrollmentResponse.model_validate(dict(row.one()._mapping))

    async def list_enrolled(
        self, program_id: int, status: str = "active"
    ) -> List[EnrollmentResponse]:
        rows = await self._session.execute(
            text("""
                SELECT id, program_id, patient_id, enrolled_at,
                       enrolled_by, status, notes
                FROM   program_enrollments
                WHERE  program_id = :pid AND status = :status
                ORDER  BY enrolled_at DESC
            """),
            {"pid": program_id, "status": status},
        )
        return [EnrollmentResponse.model_validate(dict(r._mapping)) for r in rows]

    async def discharge(self, program_id: int, patient_id: int) -> None:
        await self._session.execute(
            text("""
                UPDATE program_enrollments
                SET    status = 'discharged'
                WHERE  program_id = :pid AND patient_id = :patient_id
            """),
            {"pid": program_id, "patient_id": patient_id},
        )
        await self._session.commit()

    # ── Relatórios ───────────────────────────────────────────

    async def overdue_patients(
        self, program_id: int, threshold_days: int = 30
    ) -> List[OverduePatient]:
        """Pacientes matriculados sem visita há mais de `threshold_days` dias."""
        rows = await self._session.execute(
            text("""
                SELECT
                    p.id                                           AS patient_id,
                    p.full_name,
                    MAX(e.started_at)                              AS last_encounter_date,
                    EXTRACT(DAY FROM NOW() - MAX(e.started_at))::INT AS days_without_visit
                FROM   program_enrollments pe
                JOIN   patients   p ON p.id = pe.patient_id
                LEFT   JOIN encounters e
                       ON e.patient_id = pe.patient_id
                WHERE  pe.program_id = :pid
                  AND  pe.status = 'active'
                GROUP  BY p.id, p.full_name
                HAVING MAX(e.started_at) IS NULL
                    OR EXTRACT(DAY FROM NOW() - MAX(e.started_at)) > :threshold
                ORDER  BY days_without_visit DESC NULLS FIRST
            """),
            {"pid": program_id, "threshold": threshold_days},
        )
        return [OverduePatient.model_validate(dict(r._mapping)) for r in rows]

    async def coverage(self, program_id: int, threshold_days: int = 30) -> CoverageReport:
        prog_row = await self._session.execute(
            text("SELECT id, name, target_count FROM health_programs WHERE id=:id"),
            {"id": program_id},
        )
        prog = dict(prog_row.one()._mapping)

        enrolled_row = await self._session.execute(
            text(
                "SELECT COUNT(*) FROM program_enrollments "
                "WHERE program_id=:pid AND status='active'"
            ),
            {"pid": program_id},
        )
        enrolled_count: int = enrolled_row.scalar_one()

        overdue = await self.overdue_patients(program_id, threshold_days)

        target = prog["target_count"] or 1  # evita divisão por zero
        return CoverageReport(
            program_id=prog["id"],
            program_name=prog["name"],
            target_count=prog["target_count"],
            enrolled_count=enrolled_count,
            coverage_pct=round(enrolled_count / target * 100, 2),
            overdue_count=len(overdue),
        )
```

---

## 5. Router

**`modules/programas/router.py`**

```python
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from intellicare_core.auth import get_tenant_context, require_role
from intellicare_core.context import TenantContext
from intellicare_core.db import get_tenant_session
from modules.programas.schemas import (
    CoverageReport,
    EnrollRequest,
    EnrollmentResponse,
    OverduePatient,
    ProgramCreate,
    ProgramResponse,
)
from modules.programas.service import ProgramasService

router = APIRouter(prefix="/programas", tags=["Programas de Saúde"])


def _get_service(
    session=Depends(get_tenant_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> ProgramasService:
    return ProgramasService(session, ctx)


# ── Programas ────────────────────────────────────────────────

@router.get("/", response_model=List[ProgramResponse])
async def list_programs(
    active_only: bool = True,
    _=Depends(require_role(["CLINICO", "TENANT_GESTOR"])),
    svc: ProgramasService = Depends(_get_service),
):
    return await svc.list_programs(active_only)


@router.post("/", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    body: ProgramCreate,
    _=Depends(require_role(["TENANT_GESTOR"])),
    svc: ProgramasService = Depends(_get_service),
):
    return await svc.create_program(body)


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_program(
    program_id: int,
    _=Depends(require_role(["TENANT_GESTOR"])),
    svc: ProgramasService = Depends(_get_service),
):
    await svc.deactivate_program(program_id)


# ── Matrículas ───────────────────────────────────────────────

@router.post(
    "/{program_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_patient(
    program_id: int,
    body: EnrollRequest,
    _=Depends(require_role(["CLINICO", "TENANT_GESTOR"])),
    svc: ProgramasService = Depends(_get_service),
):
    return await svc.enroll(program_id, body)


@router.get("/{program_id}/patients", response_model=List[EnrollmentResponse])
async def list_enrolled(
    program_id: int,
    status: str = "active",
    _=Depends(require_role(["CLINICO", "TENANT_GESTOR"])),
    svc: ProgramasService = Depends(_get_service),
):
    return await svc.list_enrolled(program_id, status)


@router.delete("/{program_id}/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def discharge_patient(
    program_id: int,
    patient_id: int,
    _=Depends(require_role(["CLINICO", "TENANT_GESTOR"])),
    svc: ProgramasService = Depends(_get_service),
):
    await svc.discharge(program_id, patient_id)


# ── Relatórios ───────────────────────────────────────────────

@router.get("/{program_id}/overdue", response_model=List[OverduePatient])
async def overdue_patients(
    program_id: int,
    threshold_days: int = 30,
    _=Depends(require_role(["CLINICO", "TENANT_GESTOR"])),
    svc: ProgramasService = Depends(_get_service),
):
    return await svc.overdue_patients(program_id, threshold_days)


@router.get("/{program_id}/coverage", response_model=CoverageReport)
async def coverage_report(
    program_id: int,
    threshold_days: int = 30,
    _=Depends(require_role(["TENANT_GESTOR"])),
    svc: ProgramasService = Depends(_get_service),
):
    return await svc.coverage(program_id, threshold_days)
```

---

## 6. Module Entry Point

**`modules/programas/main.py`**

```python
from fastapi import APIRouter
from intellicare_core.base_module import BaseModule
from modules.programas.router import router


class Module(BaseModule):
    name = "programas"
    version = "1.0.0"

    def get_router(self) -> APIRouter:
        return router

    async def health(self) -> dict:
        return {"status": "ok", "module": self.name, "version": self.version}
```

---

## 7. Testes Unitários

**`tests/programas/test_programas_service.py`**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from modules.programas.service import ProgramasService
from modules.programas.schemas import ProgramCreate, EnrollRequest
from intellicare_core.context import TenantContext


@pytest.fixture
def ctx():
    return TenantContext(
        tenant_id="t1", schema="tenant_demo",
        user_id="u1", roles=["CLINICO"], email="clinico@demo.com"
    )


@pytest.fixture
def svc(ctx):
    session = AsyncMock()
    return ProgramasService(session, ctx)


@pytest.mark.asyncio
async def test_create_program(svc):
    mock_row = MagicMock()
    mock_row._mapping = {
        "id": 1, "name": "Hipertensão", "description": None,
        "target_count": 100, "active": True,
        "created_by": "u1", "created_at": None, "updated_at": None
    }
    svc._session.execute.return_value.one.return_value = mock_row
    result = await svc.create_program(ProgramCreate(name="Hipertensão", target_count=100))
    assert result.name == "Hipertensão"
    assert result.target_count == 100


@pytest.mark.asyncio
async def test_enroll_patient(svc):
    mock_row = MagicMock()
    mock_row._mapping = {
        "id": 10, "program_id": 1, "patient_id": 5,
        "enrolled_at": None, "enrolled_by": "u1",
        "status": "active", "notes": None
    }
    svc._session.execute.return_value.one.return_value = mock_row
    result = await svc.enroll(1, EnrollRequest(patient_id=5))
    assert result.patient_id == 5
    assert result.status == "active"


@pytest.mark.asyncio
async def test_coverage_report(svc):
    # mock program row
    prog_mock = MagicMock()
    prog_mock._mapping = {"id": 1, "name": "Hipertensão", "target_count": 100}
    # mock enrolled count
    count_mock = MagicMock()
    count_mock.scalar_one.return_value = 45
    svc._session.execute.side_effect = [
        MagicMock(one=lambda: prog_mock),
        count_mock,
        MagicMock(__iter__=lambda s: iter([])),  # overdue → empty
    ]
    with patch.object(svc, "overdue_patients", return_value=[]):
        result = await svc.coverage(1)
    assert result.enrolled_count == 45
    assert result.coverage_pct == 45.0
```

---

## 8. Integração no ModuleLoader

Adicionar em `intellicare_core/module_loader.py`:

```python
from modules.programas.main import Module as ProgramasModule
# ...
loader.register(ProgramasModule())
```

E rodar a migration:

```bash
psql "$TENANT_DSN" -f db/tenant_migrations/005_programas_tables.sql
```

---

## 9. Checklist de Aceite Técnico

- [ ] Migration 005 aplica sem erros em schema de teste
- [ ] `UNIQUE (program_id, patient_id)` previne dupla matrícula
- [ ] `enroll()` com ON CONFLICT reativa paciente suspenso
- [ ] `overdue_patients()` retorna corretamente para pacientes sem nenhuma consulta
- [ ] `coverage()` retorna `coverage_pct=0` quando `enrolled_count=0`
- [ ] CLINICO não acessa `POST /programas/` (403)
- [ ] TENANT_GESTOR acessa todos os endpoints
- [ ] Testes unitários passam com `pytest tests/programas/ -v`
