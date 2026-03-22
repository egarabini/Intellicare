from fastapi import APIRouter, Depends
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error
from intellicare_core.auth.jwt import get_current_tenant
from modules.oswaldo.contracts import (
    CreatePrescriptionRequest, Prescription, CID10Result,
    OswaldoSuggestRequest, OswaldoSuggestion,
)
from modules.oswaldo import repository
from modules.oswaldo import services as oswaldo_service

router = APIRouter(tags=["oswaldo"])


@router.post("/suggest", response_model=OswaldoSuggestion)
async def suggest(
    req: OswaldoSuggestRequest,
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    return await oswaldo_service.suggest(ctx, req)


@router.get("/cid10/search", response_model=list[CID10Result])
async def search_cid10(
    q: str,
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    if len(q) < 2:
        return []
    return await repository.search_cid10(ctx, q)


@router.post("/prescriptions", response_model=Prescription)
async def create_prescription(
    req: CreatePrescriptionRequest,
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    return await repository.create_prescription(ctx, req, ctx.user_id, ctx.email or "Clinico Logado")


@router.get("/prescriptions/encounter/{encounter_id}", response_model=list[Prescription])
async def list_prescriptions(
    encounter_id: str,
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    return await repository.get_prescriptions_by_encounter(ctx, encounter_id)

from fastapi.responses import Response

@router.get("/prescriptions/{prescription_id}/receituario.pdf")
async def get_receituario_pdf(
    prescription_id: int,
    type: str = "simple",
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    pdf_bytes = await oswaldo_service.generate_receituario(ctx, prescription_id, type)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="receituario_{prescription_id}.pdf"'}
    )
