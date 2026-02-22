"""Endpoints REST para conformidade LGPD."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.audit.audit_service import AuditTrailService
from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.data_subject_service import DataSubjectService
from comunicacao.lgpd.preferences_service import PreferencesService
from comunicacao.storage.repository import get_db_session

router = APIRouter(prefix="/api/v1/lgpd", tags=["LGPD"])

# ── Schemas ──


class PreferencesResponse(BaseModel):
    """Response de preferências."""
    
    patient_id: str
    rocketchat_enabled: bool
    email_enabled: bool
    sms_enabled: bool
    whatsapp_enabled: bool
    push_enabled: bool
    jitsi_enabled: bool
    quiet_hours: Optional[Dict[str, str]]
    consent_given: bool
    consent_given_at: Optional[str]
    consent_version: Optional[str]
    consent_expires_at: Optional[str]


class UpdatePreferencesRequest(BaseModel):
    """Request para atualizar preferências."""
    
    rocketchat_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    jitsi_enabled: Optional[bool] = None


class SetQuietHoursRequest(BaseModel):
    """Request para configurar quiet hours."""
    
    start: str = Field(pattern=r"^\d{2}:\d{2}$", description="Horário de início (HH:MM)")
    end: str = Field(pattern=r"^\d{2}:\d{2}$", description="Horário de fim (HH:MM)")


class GrantConsentRequest(BaseModel):
    """Request para conceder consentimento."""
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConsentHistoryResponse(BaseModel):
    """Response de histórico de consentimento."""
    
    patient_id: str
    history: List[Dict[str, Any]]


class ExportDataResponse(BaseModel):
    """Response de exportação de dados."""
    
    patient_id: str
    exported_at: str
    format: str
    data: Dict[str, Any]


class AnonymizeResponse(BaseModel):
    """Response de anonimização."""
    
    patient_id: str
    anonymized_at: str
    counts_before: Dict[str, int]
    audit_trail_retained: bool
    note: str


class ComplianceReportResponse(BaseModel):
    """Response de relatório de conformidade."""
    
    period: str
    total_communications: int
    by_legal_basis: Dict[str, int]
    critical_overrides: int
    blocked_by_lgpd: int
    opt_out_rate: float
    consent_coverage: float
    chain_integrity: bool


# ── Dependencies ──


def get_lgpd_config() -> LGPDConfig:
    """Dependency para LGPDConfig."""
    return LGPDConfig.from_env()


def get_preferences_service(
    db: AsyncSession = Depends(get_db_session),
    config: LGPDConfig = Depends(get_lgpd_config),
) -> PreferencesService:
    """Dependency para PreferencesService."""
    return PreferencesService(db, config)


def get_data_subject_service(
    db: AsyncSession = Depends(get_db_session),
    config: LGPDConfig = Depends(get_lgpd_config),
) -> DataSubjectService:
    """Dependency para DataSubjectService."""
    return DataSubjectService(db, config)


def get_audit_service(
    db: AsyncSession = Depends(get_db_session),
    config: LGPDConfig = Depends(get_lgpd_config),
) -> AuditTrailService:
    """Dependency para AuditTrailService."""
    return AuditTrailService(db, config)


# ── Endpoints de Preferências ──


@router.get("/preferences/{patient_id}", response_model=PreferencesResponse)
async def get_preferences(
    patient_id: str,
    service: PreferencesService = Depends(get_preferences_service),
):
    """
    Busca preferências de comunicação do paciente.
    
    **Auth**: Requer role `comunicacao_read` ou `data_protection_officer`
    """
    preferences = await service.get_preferences(patient_id)
    
    if not preferences:
        # Criar preferências padrão
        preferences = await service.create_default_preferences(patient_id)
    
    return PreferencesResponse(
        patient_id=preferences.patient_id,
        rocketchat_enabled=preferences.rocketchat_enabled,
        email_enabled=preferences.email_enabled,
        sms_enabled=preferences.sms_enabled,
        whatsapp_enabled=preferences.whatsapp_enabled,
        push_enabled=preferences.push_enabled,
        jitsi_enabled=preferences.jitsi_enabled,
        quiet_hours=preferences.quiet_hours,
        consent_given=preferences.consent_given,
        consent_given_at=preferences.consent_given_at.isoformat() if preferences.consent_given_at else None,
        consent_version=preferences.consent_version,
        consent_expires_at=preferences.consent_expires_at.isoformat() if preferences.consent_expires_at else None,
    )


@router.put("/preferences/{patient_id}", response_model=PreferencesResponse)
async def update_preferences(
    patient_id: str,
    request: UpdatePreferencesRequest,
    service: PreferencesService = Depends(get_preferences_service),
):
    """
    Atualiza preferências de comunicação do paciente.

    **Auth**: Requer role `comunicacao_write` ou `data_protection_officer`
    """
    preferences = await service.update_preferences(
        patient_id=patient_id,
        rocketchat_enabled=request.rocketchat_enabled,
        email_enabled=request.email_enabled,
        sms_enabled=request.sms_enabled,
        whatsapp_enabled=request.whatsapp_enabled,
        push_enabled=request.push_enabled,
        jitsi_enabled=request.jitsi_enabled,
    )

    return PreferencesResponse(
        patient_id=preferences.patient_id,
        rocketchat_enabled=preferences.rocketchat_enabled,
        email_enabled=preferences.email_enabled,
        sms_enabled=preferences.sms_enabled,
        whatsapp_enabled=preferences.whatsapp_enabled,
        push_enabled=preferences.push_enabled,
        jitsi_enabled=preferences.jitsi_enabled,
        quiet_hours=preferences.quiet_hours,
        consent_given=preferences.consent_given,
        consent_given_at=preferences.consent_given_at.isoformat() if preferences.consent_given_at else None,
        consent_version=preferences.consent_version,
        consent_expires_at=preferences.consent_expires_at.isoformat() if preferences.consent_expires_at else None,
    )


@router.put("/preferences/{patient_id}/quiet-hours", response_model=PreferencesResponse)
async def set_quiet_hours(
    patient_id: str,
    request: SetQuietHoursRequest,
    service: PreferencesService = Depends(get_preferences_service),
):
    """
    Configura horários silenciosos do paciente.

    **Auth**: Requer role `comunicacao_write` ou `data_protection_officer`
    """
    preferences = await service.set_quiet_hours(
        patient_id=patient_id,
        start=request.start,
        end=request.end,
    )

    return PreferencesResponse(
        patient_id=preferences.patient_id,
        rocketchat_enabled=preferences.rocketchat_enabled,
        email_enabled=preferences.email_enabled,
        sms_enabled=preferences.sms_enabled,
        whatsapp_enabled=preferences.whatsapp_enabled,
        push_enabled=preferences.push_enabled,
        jitsi_enabled=preferences.jitsi_enabled,
        quiet_hours=preferences.quiet_hours,
        consent_given=preferences.consent_given,
        consent_given_at=preferences.consent_given_at.isoformat() if preferences.consent_given_at else None,
        consent_version=preferences.consent_version,
        consent_expires_at=preferences.consent_expires_at.isoformat() if preferences.consent_expires_at else None,
    )


@router.post("/preferences/{patient_id}/opt-out/{channel}")
async def opt_out_channel(
    patient_id: str,
    channel: str,
    service: PreferencesService = Depends(get_preferences_service),
):
    """
    Desabilita um canal específico (opt-out).

    **Auth**: Requer role `comunicacao_write` ou `data_protection_officer`
    """
    try:
        await service.opt_out_channel(patient_id, channel)
        return {"status": "success", "message": f"Canal {channel} desabilitado"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/preferences/{patient_id}/opt-in/{channel}")
async def opt_in_channel(
    patient_id: str,
    channel: str,
    service: PreferencesService = Depends(get_preferences_service),
):
    """
    Habilita um canal específico (opt-in).

    **Auth**: Requer role `comunicacao_write` ou `data_protection_officer`
    """
    try:
        await service.opt_in_channel(patient_id, channel)
        return {"status": "success", "message": f"Canal {channel} habilitado"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Endpoints de Consentimento ──


@router.post("/consent/{patient_id}")
async def grant_consent(
    patient_id: str,
    request: GrantConsentRequest,
    service: PreferencesService = Depends(get_preferences_service),
):
    """
    Concede consentimento para comunicações.

    **Auth**: Requer role `comunicacao_write` ou `data_protection_officer`
    """
    preferences = await service.grant_consent(
        patient_id=patient_id,
        metadata=request.metadata,
    )

    return {
        "status": "success",
        "message": "Consentimento concedido",
        "consent_given_at": preferences.consent_given_at.isoformat() if preferences.consent_given_at else None,
        "consent_version": preferences.consent_version,
        "consent_expires_at": preferences.consent_expires_at.isoformat() if preferences.consent_expires_at else None,
    }


@router.delete("/consent/{patient_id}")
async def withdraw_consent(
    patient_id: str,
    service: PreferencesService = Depends(get_preferences_service),
):
    """
    Revoga consentimento para comunicações.

    **Auth**: Requer role `comunicacao_write` ou `data_protection_officer`
    """
    await service.withdraw_consent(patient_id, metadata={})

    return {
        "status": "success",
        "message": "Consentimento revogado",
    }


@router.get("/consent/{patient_id}/history", response_model=ConsentHistoryResponse)
async def get_consent_history(
    patient_id: str,
    service: DataSubjectService = Depends(get_data_subject_service),
):
    """
    Busca histórico de consentimento do paciente.

    **Auth**: Requer role `comunicacao_read` ou `data_protection_officer`
    """
    history = await service.get_consent_history(patient_id)

    return ConsentHistoryResponse(
        patient_id=patient_id,
        history=history,
    )


# ── Endpoints de Auditoria ──


@router.get("/audit")
async def list_audit_entries(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    channel: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    legal_basis: str | None = Query(default=None),
    lgpd_override: bool | None = Query(default=None),
    patient_id: str | None = Query(default=None),
    source_module: str | None = Query(default=None),
    from_dt: datetime | None = Query(default=None),
    to_dt: datetime | None = Query(default=None),
    service: AuditTrailService = Depends(get_audit_service),
):
    """
    Lista entradas de audit trail.

    **Auth**: Requer role `data_protection_officer` ou `audit_read`
    """
    total, entries = await service.list_audit_entries(
        limit=limit,
        offset=offset,
        channel=channel,
        status=status,
        severity=severity,
        legal_basis=legal_basis,
        lgpd_override=lgpd_override,
        patient_id=patient_id,
        source_module=source_module,
        from_dt=from_dt,
        to_dt=to_dt,
    )
    return {
        "status": "success",
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(entry.id),
                "intent_id": entry.intent_id,
                "delivery_id": entry.delivery_id,
                "channel": entry.channel,
                "status": entry.status,
                "severity": entry.severity,
                "legal_basis": entry.legal_basis,
                "lgpd_override": entry.lgpd_override,
                "source_module": entry.source_module,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ],
    }


@router.get("/audit/{intent_id}")
async def get_audit_by_intent(
    intent_id: str,
    service: AuditTrailService = Depends(get_audit_service),
):
    """
    Busca audit entries por intent_id.

    **Auth**: Requer role `data_protection_officer` ou `audit_read`
    """
    from uuid import UUID

    try:
        intent_uuid = UUID(intent_id)
        entries = await service.get_audit_by_intent(intent_uuid)

        return {
            "intent_id": intent_id,
            "total": len(entries),
            "entries": [
                {
                    "id": str(entry.id),
                    "channel": entry.channel,
                    "status": entry.status,
                    "severity": entry.severity,
                    "legal_basis": entry.legal_basis,
                    "lgpd_override": entry.lgpd_override,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in entries
            ],
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="intent_id inválido")


@router.get("/audit/patient/{patient_id}")
async def get_audit_by_patient(
    patient_id: str,
    limit: int = Query(default=100, le=1000),
    service: AuditTrailService = Depends(get_audit_service),
):
    """
    Busca audit entries por patient_id.

    **Auth**: Requer role `data_protection_officer` ou `audit_read`
    """
    entries = await service.get_audit_by_patient(patient_id, limit)

    return {
        "patient_id": patient_id,
        "total": len(entries),
        "entries": [
            {
                "id": str(entry.id),
                "intent_id": entry.intent_id,
                "channel": entry.channel,
                "status": entry.status,
                "severity": entry.severity,
                "legal_basis": entry.legal_basis,
                "lgpd_override": entry.lgpd_override,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ],
    }


# ── Endpoints de Direitos do Titular ──


@router.get("/export/{patient_id}", response_model=ExportDataResponse)
async def export_patient_data(
    patient_id: str,
    format: str = Query(default="json", pattern="^(json|fhir)$"),
    service: DataSubjectService = Depends(get_data_subject_service),
):
    """
    Exporta todos os dados do paciente (Art. 18, II e V - Portabilidade).

    **Auth**: Requer role `data_protection_officer` ou `patient_self`
    """
    data = await service.export_data(patient_id, format)

    return ExportDataResponse(
        patient_id=patient_id,
        exported_at=data.get("exported_at", "now"),
        format=format,
        data=data,
    )


@router.post("/anonymize/{patient_id}", response_model=AnonymizeResponse)
async def anonymize_patient_data(
    patient_id: str,
    service: DataSubjectService = Depends(get_data_subject_service),
):
    """
    Anonimiza dados do paciente (Art. 18, IV).

    **ATENÇÃO**: Operação irreversível!

    **Auth**: Requer role `data_protection_officer`
    """
    result = await service.anonymize(patient_id)

    return AnonymizeResponse(
        patient_id=result["patient_id"],
        anonymized_at=result["anonymized_at"],
        counts_before=result["counts_before"],
        audit_trail_retained=result["audit_trail_retained"],
        note=result["note"],
    )


# ── Endpoints de Conformidade ──


@router.get("/compliance-report", response_model=ComplianceReportResponse)
async def get_compliance_report(
    period: str = Query(default="month", pattern="^(month|quarter|year)$"),
    service: AuditTrailService = Depends(get_audit_service),
):
    """
    Relatório de conformidade LGPD.

    **Auth**: Requer role `data_protection_officer`
    """
    metrics = await service.compute_compliance_report(period)
    return ComplianceReportResponse(
        period=period,
        total_communications=int(metrics["total_communications"]),
        by_legal_basis=dict(metrics["by_legal_basis"]),
        critical_overrides=int(metrics["critical_overrides"]),
        blocked_by_lgpd=int(metrics["blocked_by_lgpd"]),
        opt_out_rate=float(metrics["opt_out_rate"]),
        consent_coverage=float(metrics["consent_coverage"]),
        chain_integrity=bool(metrics["chain_integrity"]),
    )


@router.get("/verify-chain")
async def verify_chain_integrity(
    service: AuditTrailService = Depends(get_audit_service),
):
    """
    Verifica integridade da hash chain.

    **Auth**: Requer role `data_protection_officer` ou `audit_read`
    """
    is_valid, error_message = await service.verify_chain_integrity()

    if is_valid:
        return {
            "status": "success",
            "chain_integrity": True,
            "message": "Hash chain íntegra - nenhuma adulteração detectada",
        }
    else:
        return {
            "status": "error",
            "chain_integrity": False,
            "message": "Hash chain comprometida!",
            "error": error_message,
        }
