"""CuidadoService — logica de negocio do modulo clinico."""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session

logger = logging.getLogger("intellicare.cuidado")


class CuidadoService:
    """CRUD de pacientes, consultas e evoluções SOAP."""

    # ------------------------------------------------------------------
    # Pacientes
    # ------------------------------------------------------------------

    async def create_patient(self, ctx: TenantContext, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        "INSERT INTO patients (full_name,cpf,birth_date,sex,phone,email,address) "
                        "VALUES (:full_name,:cpf,:birth_date,:sex,:phone,:email,:address) RETURNING *"
                    ),
                    data,
                )
            ).mappings().first()
        return dict(row)

    async def search_patients(self, ctx: TenantContext, q: str, limit: int = 20) -> list[dict]:
        async with tenant_session(ctx) as db:
            if q and q.strip():
                rows = (
                    await db.execute(
                        text(
                            "SELECT * FROM patients WHERE active=true "
                            "AND to_tsvector('portuguese',full_name) @@ plainto_tsquery('portuguese',:q) "
                            "ORDER BY full_name LIMIT :lim"
                        ),
                        {"q": q, "lim": limit},
                    )
                ).mappings().all()
            else:
                rows = (
                    await db.execute(
                        text("SELECT * FROM patients WHERE active=true ORDER BY full_name LIMIT :lim"),
                        {"lim": limit},
                    )
                ).mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Consultas (Encounters)
    # ------------------------------------------------------------------

    async def open_encounter(self, ctx: TenantContext, clinician_id: str, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        "INSERT INTO encounters (patient_id,clinician_id,chief_complaint,priority) "
                        "VALUES (:patient_id,:clinician_id,:chief_complaint,:priority) RETURNING *"
                    ),
                    {"clinician_id": clinician_id, **data},
                )
            ).mappings().first()
        return dict(row)

    async def add_note(
        self, ctx: TenantContext, encounter_id: UUID, clinician_id: str, data: dict,
    ) -> dict:
        async with tenant_session(ctx) as db:
            enc = (
                await db.execute(
                    text("SELECT status FROM encounters WHERE id=:id"),
                    {"id": str(encounter_id)},
                )
            ).first()
            if not enc or enc[0] != "open":
                raise ValueError("Consulta não encontrada ou já encerrada")
            row = (
                await db.execute(
                    text(
                        "INSERT INTO encounter_notes (encounter_id,clinician_id,subjective,objective,assessment,plan) "
                        "VALUES (:eid,:cid,:subjective,:objective,:assessment,:plan) RETURNING *"
                    ),
                    {"eid": str(encounter_id), "cid": clinician_id, **data},
                )
            ).mappings().first()
        return dict(row)

    async def close_encounter(self, ctx: TenantContext, encounter_id: UUID) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        "UPDATE encounters SET status='closed',closed_at=now() "
                        "WHERE id=:id AND status='open' RETURNING *"
                    ),
                    {"id": str(encounter_id)},
                )
            ).mappings().first()
            if not row:
                raise LookupError("Consulta não encontrada ou já encerrada")
        return dict(row)

    async def patient_history(self, ctx: TenantContext, patient_id: UUID) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text("SELECT * FROM encounters WHERE patient_id=:pid ORDER BY opened_at DESC"),
                    {"pid": str(patient_id)},
                )
            ).mappings().all()
        return [dict(r) for r in rows]

