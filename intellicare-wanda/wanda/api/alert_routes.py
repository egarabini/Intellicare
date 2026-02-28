"""API routes for AlertHub (EF-W007)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------

class AlertRequest(BaseModel):
    patient_id: str
    source_agent: str
    alert_type: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    title: str
    description: str = ""
    recommended_action: str = ""
    clinical_data: dict = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str


class ResolveRequest(BaseModel):
    resolved_by: str
    resolution_notes: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get_hub(request: Request):  # type: ignore[return]
    hub = getattr(request.app.state, "alert_hub", None)
    if hub is None:
        raise HTTPException(status_code=503, detail="AlertHub nao disponivel (enable_alert_hub=False)")
    return hub


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("", summary="Recebe alerta de um agente")
async def receive_alert(body: AlertRequest, request: Request):
    from wanda.alerts.models import ClinicalAlert  # noqa: PLC0415

    hub = _get_hub(request)
    alert = ClinicalAlert(
        patient_id=body.patient_id,
        source_agent=body.source_agent,
        alert_type=body.alert_type,
        severity=body.severity,
        title=body.title,
        description=body.description,
        recommended_action=body.recommended_action,
        clinical_data=body.clinical_data,
        idempotency_key=body.idempotency_key,
    )
    result = await hub.receive_alert(alert)
    return {
        "alert_id": result.alert_id,
        "status": result.status,
        "priority_score": result.priority_score,
        "message": result.message,
    }


@router.get("/queue", summary="Fila de alertas pendentes")
async def get_alert_queue(
    request: Request,
    limit: int = 50,
    patient_id: Optional[str] = None,
):
    hub = _get_hub(request)
    alerts = hub.get_pending_alerts(limit=limit, patient_id=patient_id)
    return {"total": len(alerts), "alerts": alerts}


@router.put("/{alert_id}/acknowledge", summary="Reconhecer alerta")
async def acknowledge_alert(alert_id: str, body: AcknowledgeRequest, request: Request):
    hub = _get_hub(request)
    ok = hub.acknowledge_alert(alert_id, body.acknowledged_by)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Alerta {alert_id} nao encontrado")
    return {"alert_id": alert_id, "status": "acknowledged"}


@router.put("/{alert_id}/resolve", summary="Resolver alerta")
async def resolve_alert(alert_id: str, body: ResolveRequest, request: Request):
    hub = _get_hub(request)
    ok = hub.resolve_alert(alert_id, body.resolved_by, body.resolution_notes)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Alerta {alert_id} nao encontrado")
    return {"alert_id": alert_id, "status": "resolved"}


@router.get("/patient/{patient_id}", summary="Alertas do paciente")
async def get_patient_alerts(patient_id: str, request: Request):
    hub = _get_hub(request)
    alerts = hub.get_pending_alerts(limit=100, patient_id=patient_id)
    return {"patient_id": patient_id, "total": len(alerts), "alerts": alerts}


@router.get("/stats", summary="Metricas de alertas")
async def get_alert_stats(request: Request):
    hub = _get_hub(request)
    return hub.get_stats()
