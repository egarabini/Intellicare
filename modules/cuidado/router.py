"""Cuidado Router — endpoints REST do modulo clinico."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from modules.slm.service import SLMService
from intellicare_core.auth.jwt import get_current_tenant
from .schemas import (
    ClinicalAskRequest, EncounterCreate, NoteCreate, PatientCreate,
    PatientClinicalUpdate, EncounterUpdate, PacienteMeUpdate,
    GroupCreate, GroupUpdate, AddMember, ProfessionalCreate, ProfessionalUpdate,
)
from .service import CuidadoService

router = APIRouter(tags=["cuidado"])
_svc = CuidadoService()
_slm = SLMService()
Clinico = Annotated[TenantContext, Depends(require_role("CLINICO"))]
Paciente = Annotated[TenantContext, Depends(require_role("PACIENTE"))]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "cuidado", "version": "1.0.0"}


@router.get("/cid10")
async def search_cid10(ctx: Clinico, q: str, limit: int = 10):
    return await _svc.search_cid10(q, limit)

@router.post("/patients", status_code=201)
async def create_patient(p: PatientCreate, ctx: Clinico):
    return await _svc.create_patient(ctx, p.model_dump())

@router.get("/my-agenda")
async def my_agenda(ctx: Clinico, date: str | None = None, from_: str | None = None, to: str | None = None):
    # Depending on query params map to service
    if date:
        return await _svc.get_agenda(ctx, ctx.user_id, date, date)
    elif from_ and to:
        return await _svc.get_agenda(ctx, ctx.user_id, from_, to)
    else:
        # Default to today
        from datetime import date as d
        return await _svc.get_agenda(ctx, ctx.user_id, str(d.today()), str(d.today()))

@router.get("/patients/{pid}/profile")
async def patient_profile(pid: UUID, ctx: Clinico):
    return await _svc.get_patient_profile(ctx, pid)

@router.patch("/patients/{pid}/clinical")
async def update_clinical(pid: UUID, p: PatientClinicalUpdate, ctx: Clinico):
    return await _svc.update_patient_clinical(ctx, pid, p.model_dump(exclude_unset=True))


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


@router.patch("/encounters/{eid}")
async def update_encounter(eid: UUID, u: EncounterUpdate, ctx: Clinico):
    try:
        return await _svc.update_encounter(ctx, eid, u.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/encounters/{eid}/ask")
async def clinical_ask(eid: UUID, req: ClinicalAskRequest, ctx: Clinico):
    try:
        return await _slm.ask(req.query, ctx, req.limit, req.min_similarity)
    except (ConnectionError, RuntimeError) as e:
        raise HTTPException(503, str(e))


# ── Endpoints do Paciente ────────────────────────────────────────────────────

@router.get("/paciente/painel")
async def paciente_painel(ctx: Paciente):
    return await _svc.paciente_painel(ctx)


@router.get("/paciente/appointments")
async def paciente_appointments(ctx: Paciente, status: str = "upcoming"):
    return await _svc.paciente_appointments(ctx, status)


@router.patch("/paciente/appointments/{appt_id}/confirm")
async def paciente_confirm_appointment(appt_id: UUID, ctx: Paciente):
    return await _svc.paciente_confirm_appointment(ctx, appt_id)


@router.delete("/paciente/appointments/{appt_id}")
async def paciente_cancel_appointment(appt_id: UUID, ctx: Paciente):
    return await _svc.paciente_cancel_appointment(ctx, appt_id)


@router.get("/paciente/history")
async def paciente_history(ctx: Paciente, page: int = 1, size: int = 10):
    return await _svc.paciente_history(ctx, page, size)


@router.get("/paciente/programs")
async def paciente_programs(ctx: Paciente):
    return await _svc.paciente_programs(ctx)


@router.get("/paciente/me")
async def paciente_me(ctx: Paciente):
    return await _svc.paciente_me(ctx)


@router.patch("/paciente/me")
async def paciente_update_me(body: PacienteMeUpdate, ctx: Paciente):
    return await _svc.paciente_update_me(ctx, body.model_dump(exclude_unset=True))


@router.get("/paciente/clinic-info")
async def paciente_clinic_info(ctx: Paciente):
    return await _svc.paciente_clinic_info(ctx)


# ── DEM-032: Grupos de Profissionais ─────────────────────────────────────────

@router.get("/groups")
async def list_groups(ctx: Clinico):
    return await _svc.list_groups(ctx)


@router.post("/groups", status_code=201)
async def create_group(body: GroupCreate, ctx: Clinico):
    return await _svc.create_group(ctx, body.model_dump())


@router.get("/groups/{group_id}")
async def get_group(group_id: int, ctx: Clinico):
    try:
        return await _svc.get_group(ctx, group_id)
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.patch("/groups/{group_id}")
async def update_group(group_id: int, body: GroupUpdate, ctx: Clinico):
    try:
        return await _svc.update_group(ctx, group_id, body.model_dump(exclude_unset=True))
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.patch("/groups/{group_id}/status")
async def toggle_group_status(group_id: int, ctx: Clinico):
    try:
        return await _svc.toggle_group_status(ctx, group_id)
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.get("/groups/{group_id}/members")
async def list_group_members(group_id: int, ctx: Clinico):
    return await _svc.list_group_members(ctx, group_id)


@router.post("/groups/{group_id}/members", status_code=201)
async def add_member(group_id: int, body: AddMember, ctx: Clinico):
    try:
        return await _svc.add_member(ctx, group_id, body.professional_id)
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.delete("/groups/{group_id}/members/{prof_id}")
async def remove_member(group_id: int, prof_id: int, ctx: Clinico):
    try:
        return await _svc.remove_member(ctx, group_id, prof_id)
    except LookupError as e:
        raise HTTPException(404, str(e))


# ── DEM-032: Profissionais ───────────────────────────────────────────────────

@router.get("/professionals")
async def list_professionals(ctx: Clinico, unit_id: int | None = None,
                              specialty: str | None = None, group_id: int | None = None,
                              status: str | None = None):
    return await _svc.list_professionals(ctx, unit_id, specialty, group_id, status)


@router.post("/professionals", status_code=201)
async def create_professional(body: ProfessionalCreate, ctx: Clinico):
    return await _svc.create_professional(ctx, body.model_dump())


@router.get("/professionals/{prof_id}")
async def get_professional(prof_id: int, ctx: Clinico):
    try:
        return await _svc.get_professional(ctx, prof_id)
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.patch("/professionals/{prof_id}")
async def update_professional(prof_id: int, body: ProfessionalUpdate, ctx: Clinico):
    try:
        return await _svc.update_professional(ctx, prof_id, body.model_dump(exclude_unset=True))
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.patch("/professionals/{prof_id}/status")
async def toggle_professional_status(prof_id: int, ctx: Clinico):
    try:
        return await _svc.toggle_professional_status(ctx, prof_id)
    except LookupError as e:
        raise HTTPException(404, str(e))


# ── DEM-032: Usuários Clínicos ───────────────────────────────────────────────

@router.get("/clinical-users")
async def list_clinical_users(ctx: Clinico):
    return await _svc.list_clinical_users(ctx)


@router.get("/dashboard-team-stats")
async def dashboard_team_stats(ctx: Clinico):
    return await _svc.dashboard_team_stats(ctx)
