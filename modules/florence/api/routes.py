from fastapi import APIRouter, Depends
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error
from intellicare_core.auth.jwt import get_current_tenant
from modules.florence.contracts import CreateNoteRequest, ClinicalNote
from modules.florence import repository

router = APIRouter(prefix="/florence", tags=["florence"])


@router.post("/notes", response_model=ClinicalNote)
async def create_note(
    req: CreateNoteRequest,
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    return await repository.create_note(ctx, req, ctx.user.sub, ctx.user.name)


@router.get("/notes/encounter/{encounter_id}", response_model=list[ClinicalNote])
async def list_notes_by_encounter(
    encounter_id: int,
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    return await repository.get_notes_by_encounter(ctx, encounter_id)


@router.get("/notes/patient/{patient_id}", response_model=list[ClinicalNote])
async def list_notes_by_patient(
    patient_id: int,
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    return await repository.get_notes_by_patient(ctx, patient_id)
