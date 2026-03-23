from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from intellicare_core.auth.jwt import get_current_tenant, require_role
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error
from modules.oswaldo import repository
from modules.oswaldo import services as oswaldo_service
from modules.oswaldo.contracts import (
    CID10Result,
    CertificateStatusOut,
    CertificateUploadResponse,
    CheckInteractionsRequest,
    CheckInteractionsResponse,
    CreatePrescriptionRequest,
    OswaldoSuggestion,
    OswaldoSuggestRequest,
    Prescription,
)
from modules.oswaldo.interactions import check_interactions

router = APIRouter(tags=["oswaldo"])


@router.post("/suggest", response_model=OswaldoSuggestion)
async def suggest(req: OswaldoSuggestRequest, ctx: TenantContext = Depends(get_current_tenant)):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    return await oswaldo_service.suggest(ctx, req)


@router.get("/cid10/search", response_model=list[CID10Result])
async def search_cid10(q: str, ctx: TenantContext = Depends(get_current_tenant)):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    if len(q) < 2:
        return []
    return await repository.search_cid10(ctx, q)


@router.post("/prescriptions", response_model=Prescription)
async def create_prescription(req: CreatePrescriptionRequest, ctx: TenantContext = Depends(get_current_tenant)):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    return await repository.create_prescription(ctx, req, ctx.user_id, ctx.email or "Clinico Logado")


@router.get("/prescriptions/encounter/{encounter_id}", response_model=list[Prescription])
async def list_prescriptions(encounter_id: str, ctx: TenantContext = Depends(get_current_tenant)):
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    return await repository.get_prescriptions_by_encounter(ctx, encounter_id)


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
        headers={"Content-Disposition": f'attachment; filename="receituario_{prescription_id}.pdf"'},
    )


@router.get("/paciente/me/prescriptions/{prescription_id}/receituario.pdf")
async def get_my_receituario_pdf(
    prescription_id: int,
    type: str = "simple",
    ctx: TenantContext = Depends(require_role("PACIENTE")),
):
    rx = await repository.get_prescription(ctx, prescription_id)
    if not rx:
        raise api_error(404, "not_found", "Prescrição não encontrada")

    from modules.cuidado.service import CuidadoService

    cuidado_service = CuidadoService()
    patient_id = await cuidado_service._get_patient_id_for_user(ctx)
    if not patient_id or str(rx.patient_id) != str(patient_id):
        raise api_error(403, "forbidden", "Acesso negado — prescrição de outro paciente")

    pdf_bytes = await oswaldo_service.generate_receituario(ctx, prescription_id, type)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="receituario_{prescription_id}.pdf"'},
    )


@router.post("/check-interactions", response_model=CheckInteractionsResponse)
async def api_check_interactions(
    req: CheckInteractionsRequest,
    ctx: TenantContext = Depends(get_current_tenant),
):
    if not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'CLINICO' necessaria")
    warnings, pairs_count = await check_interactions(req.medications)
    return CheckInteractionsResponse(warnings=warnings, checked_pairs=pairs_count)


@router.post("/professionals/me/certificate", status_code=201, response_model=CertificateUploadResponse)
async def upload_certificate(
    file: UploadFile = File(...),
    password: str = Form(...),
    ctx: TenantContext = Depends(require_role("CLINICO")),
):
    if not file.filename or not file.filename.lower().endswith(".pfx"):
        raise api_error(400, "invalid_file", "Apenas arquivos .pfx sao aceitos")
    pfx_bytes = await file.read()
    if len(pfx_bytes) > 50_000:
        raise api_error(400, "file_too_large", "Certificado excede 50KB")

    from modules.oswaldo.pdf_signer import extract_certificate_info
    try:
        cert_info = extract_certificate_info(pfx_bytes, password)
    except Exception:
        raise api_error(400, "invalid_certificate", "Certificado invalido ou senha incorreta")

    prof = await repository.get_professional_by_keycloak_id(ctx, ctx.user_id)
    if not prof:
        raise api_error(404, "not_found", "Profissional nao encontrado")

    from intellicare_core.crypto import encrypt_bytes, encrypt_text
    row = await repository.upsert_professional_certificate(
        ctx,
        professional_id=prof["id"],
        pfx_encrypted=encrypt_bytes(pfx_bytes),
        password_hash=encrypt_text(password),
        subject_name=cert_info["subject_name"],
        valid_until=cert_info["valid_until"],
    )
    return CertificateUploadResponse(
        subject_name=row["subject_name"],
        valid_until=row["valid_until"],
        uploaded_at=row["uploaded_at"],
    )


@router.get("/professionals/me/certificate", response_model=CertificateStatusOut)
async def get_certificate_status(ctx: TenantContext = Depends(require_role("CLINICO"))):
    prof = await repository.get_professional_by_keycloak_id(ctx, ctx.user_id)
    if not prof:
        raise api_error(404, "not_found", "Profissional nao encontrado")
    cert = await repository.get_professional_certificate(ctx, prof["id"])
    if not cert:
        return CertificateStatusOut(has_certificate=False)
    return CertificateStatusOut(
        has_certificate=True,
        subject_name=cert["subject_name"],
        valid_until=cert["valid_until"],
    )


@router.delete("/professionals/me/certificate", status_code=204)
async def delete_certificate(ctx: TenantContext = Depends(require_role("CLINICO"))):
    prof = await repository.get_professional_by_keycloak_id(ctx, ctx.user_id)
    if not prof:
        raise api_error(404, "not_found", "Profissional nao encontrado")
    deleted = await repository.delete_professional_certificate(ctx, prof["id"])
    if not deleted:
        raise api_error(404, "not_found", "Certificado nao encontrado")
    return Response(status_code=204)
