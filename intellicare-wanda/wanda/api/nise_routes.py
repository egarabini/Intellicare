"""API routes for Dr. Nise / FLOWISE chatbot (EF-W013)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/chat", tags=["nise"])


class PatientChatRequest(BaseModel):
    patient_id: str
    content: str
    session_id: Optional[str] = None
    channel: str = "web"


def _get_gateway(request: Request):  # type: ignore[return]
    gateway = getattr(request.app.state, "nise_gateway", None)
    if gateway is None:
        raise HTTPException(status_code=503, detail="Dr. Nise nao disponivel (enable_dr_nise=False)")
    return gateway


@router.post("/patient", summary="Mensagem do paciente para Dr. Nise")
async def patient_chat(body: PatientChatRequest, request: Request):
    from wanda.nise.models import PatientMessage  # noqa: PLC0415

    gateway = _get_gateway(request)
    msg = PatientMessage(
        patient_id=body.patient_id,
        content=body.content,
        session_id=body.session_id,
        channel=body.channel,
    )
    response = await gateway.chat(msg)
    return {
        "session_id": response.session_id,
        "text": response.text,
        "flagged": response.flagged,
        "escalated": response.escalated,
        "message_count": response.message_count,
    }


@router.get("/patient/session/{session_id}", summary="Histórico da sessão")
async def get_session_history(session_id: str, patient_id: str, request: Request):
    gateway = _get_gateway(request)
    session = await gateway._sessions.get_or_create(
        patient_id=patient_id, session_id=session_id
    )
    return {
        "session_id": session.session_id,
        "patient_id": session.patient_id,
        "status": session.status.value,
        "message_count": session.message_count,
        "history": session.history,
    }


@router.delete("/patient/session/{session_id}", summary="Encerrar sessão")
async def end_session(session_id: str, patient_id: str, request: Request):
    gateway = _get_gateway(request)
    await gateway.end_session(session_id, patient_id)
    return {"session_id": session_id, "status": "ended"}


@router.get("/nise/status", summary="Disponibilidade do FLOWISE")
async def nise_status(request: Request):
    gateway = _get_gateway(request)
    healthy = await gateway.flowise_health()
    return {"flowise_available": healthy, "dr_nise": "online" if healthy else "degraded"}


@router.get("/nise/metrics", summary="Sessões ativas hoje")
async def nise_metrics(request: Request):
    _get_gateway(request)
    # Metrics would come from DB in production
    return {"message": "Metricas disponíveis via NiseSessionModel (DB)"}
