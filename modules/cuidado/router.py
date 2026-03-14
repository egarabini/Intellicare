"""Cuidado Router — endpoints REST do modulo clinico."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from modules.slm.service import SLMService
from .schemas import ClinicalAskRequest, EncounterCreate, NoteCreate, PatientCreate
from .service import CuidadoService

router = APIRouter(prefix="/cuidado", tags=["cuidado"])
_svc = CuidadoService()
_slm = SLMService()
Clinico = Annotated[TenantContext, Depends(require_role("CLINICO"))]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "cuidado", "version": "1.0.0"}


@router.post("/patients", status_code=201)
async def create_patient(p: PatientCreate, ctx: Clinico):
    return await _svc.create_patient(ctx, p.model_dump())


@router.get("/patients")
async def search_patients(ctx: Clinico, q: str = ""):
    return await _svc.search_patients(ctx, q)


@router.get("/patients/{pid}/history")
async def history(pid: UUID, ctx: Clinico):
    return await _svc.patient_history(ctx, pid)


@router.post("/encounters", status_code=201)
async def open_encounter(e: EncounterCreate, ctx: Clinico):
    return await _svc.open_encounter(ctx, ctx.user_id, e.model_dump())


@router.post("/encounters/{eid}/notes", status_code=201)
async def add_note(eid: UUID, n: NoteCreate, ctx: Clinico):
    try:
        return await _svc.add_note(ctx, eid, ctx.user_id, n.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/encounters/{eid}/close")
async def close_encounter(eid: UUID, ctx: Clinico):
    try:
        return await _svc.close_encounter(ctx, eid)
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.post("/encounters/{eid}/ask")
async def clinical_ask(eid: UUID, req: ClinicalAskRequest, ctx: Clinico):
    try:
        return await _slm.ask(req.query, ctx, req.limit, req.min_similarity)
    except (ConnectionError, RuntimeError) as e:
        raise HTTPException(503, str(e))

