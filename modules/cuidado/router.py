"""Cuidado Router — endpoints REST do modulo clinico."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from intellicare_core.auth.jwt import require_role
from intellicare_core.contracts.base import TenantContext
from intellicare_core.pdf.renderer import render_pdf
from modules.slm.service import SLMService
from intellicare_core.auth.jwt import get_current_tenant
from .schemas import (
    ClinicalAskRequest, EncounterCreate, NoteCreate, PatientCreate,
    PatientClinicalUpdate, EncounterUpdate, PacienteMeUpdate,
    PacienteClinicalNoteItem, PacienteJourneyItem, ClinicalTimelineResponse,
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


@router.get("/patients/{pid}/clinical-timeline")
async def clinical_timeline(
    pid: UUID,
    ctx: Clinico,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """DEM-071: Linha do tempo clínica unificada (encounters + notas + prescrições + care tasks)."""
    return await _svc.clinical_timeline(ctx, pid, limit, offset)


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

@router.get("/encounters/{eid}/report.pdf")
async def encounter_report(eid: UUID, ctx: Clinico):
    from modules.florence.repository import get_encounter_full
    from modules.florence.services import generate_clinical_report

    data = await get_encounter_full(ctx, str(eid))
    if not data:
        raise HTTPException(404, "Encontro não encontrado")

    pdf_bytes = generate_clinical_report(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=encontro_{eid}.pdf"},
    )


# ── Endpoints do Paciente ────────────────────────────────────────────────────

@router.get("/paciente/painel")
async def paciente_painel(ctx: Paciente):
    return await _svc.paciente_painel(ctx)


@router.get("/paciente/appointments")
async def paciente_appointments(ctx: Paciente, status: str = "upcoming"):
    return await _svc.paciente_appointments(ctx, status)


@router.patch("/paciente/appointments/{appt_id}/confirm")
async def paciente_confirm_appointment(appt_id: UUID, ctx: Paciente):
    try:
        return await _svc.paciente_confirm_appointment(ctx, appt_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/paciente/appointments/{appt_id}")
async def paciente_cancel_appointment(appt_id: UUID, ctx: Paciente):
    try:
        return await _svc.paciente_cancel_appointment(ctx, appt_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/paciente/history")
async def paciente_history(ctx: Paciente, page: int = 1, size: int = 10):
    return await _svc.paciente_history(ctx, page, size)


@router.get("/paciente/programs")
async def paciente_programs(ctx: Paciente):
    return await _svc.paciente_programs(ctx)


@router.get("/paciente/me")
async def paciente_me(ctx: Paciente):
    return await _svc.paciente_me(ctx)


@router.get("/paciente/me/journeys", response_model=list[PacienteJourneyItem])
async def paciente_me_journeys(
    ctx: Paciente,
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
):
    return await _svc.paciente_journeys(ctx, limit, offset)


@router.get("/paciente/me/clinical-notes", response_model=list[PacienteClinicalNoteItem])
async def paciente_me_clinical_notes(
    ctx: Paciente,
    limit: int = Query(20, le=50),
):
    return await _svc.paciente_clinical_notes(ctx, limit)


@router.patch("/paciente/me")
async def paciente_update_me(body: PacienteMeUpdate, ctx: Paciente):
    return await _svc.paciente_update_me(ctx, body.model_dump(exclude_unset=True))


@router.get("/paciente/clinic-info")
async def paciente_clinic_info(ctx: Paciente):
    return await _svc.paciente_clinic_info(ctx)


@router.get("/paciente/me/timeline", response_model=ClinicalTimelineResponse)
async def paciente_me_timeline(
    ctx: Paciente,
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
):
    """DEM-076: Linha do tempo do paciente com filtro de privacidade."""
    return await _svc.paciente_timeline(ctx, limit, offset)


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


# -----------------------------------------------------------------------------
# Reports (DEM-027)
# -----------------------------------------------------------------------------

@router.get("/relatorios/prontuario/{patient_id}")
async def report_prontuario(patient_id: UUID, ctx: Clinico) -> Response:
    patient = await _svc.get_patient_profile(ctx, patient_id)
    if not patient:
        raise HTTPException(404, "Paciente não encontrado")
        
    history = await _svc.patient_history(ctx, patient_id)
    
    # Mock some data for the report context using the patient profile
    mapped_consultas = []
    for h in history:
        mapped_consultas.append({
            "data": str(h.get("created_at", ""))[:10],
            "profissional": h.get("clinician_id", "Clínico"),
            "diagnostico": h.get("cid10_code", "Não informado"),
            "observacoes": h.get("notes", "")[:100] + "..." if h.get("notes") else "Nenhuma"
        })

    context = {
        "paciente_nome": getattr(patient, 'name', 'Desconhecido'),
        "paciente_nascimento": str(getattr(patient, 'birth_date', ''))[:10],
        "paciente_cpf": "***" + str(getattr(patient, 'cpf', '00000000000'))[3:9] + "**",
        "consultas": mapped_consultas,
        "profissional_logado": ctx.user_id, # Can be enriched with Keycloak name
        "crm_profissional": "N/A"
    }
    
    pdf_bytes = render_pdf("clinico_prontuario.html", context)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="prontuario_{patient_id}.pdf"'}
    )


@router.get("/relatorios/agenda")
async def report_agenda(
    ctx: Clinico,
    data: str = Query(...)
) -> Response:
    agenda = await _svc.get_agenda(ctx, ctx.user_id, data, data)
    
    mapped_agendamentos = []
    for a in agenda:
        mapped_agendamentos.append({
            "horario": a.get("start_time", ""),
            "paciente": a.get("patient_name", "Desconhecido"),
            "tipo_consulta": a.get("type", "Consulta"),
            "status": a.get("status", "Agendado")
        })

    context = {
        "data_agenda": data,
        "profissional_nome": ctx.user_id,
        "especialidade": "Clínico Geral",
        "agendamentos": mapped_agendamentos
    }
    
    pdf_bytes = render_pdf("clinico_agenda.html", context)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="agenda_{data}.pdf"'}
    )
