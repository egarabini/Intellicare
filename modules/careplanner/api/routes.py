"""Rotas FastAPI do modulo CarePlanner."""
from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from pydantic import BaseModel, Field

from intellicare_core.auth.jwt import get_current_tenant, require_role
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error

from ..services import CareplannerService, build_careplanner_service

router = APIRouter()


class OpenTaskRequest(BaseModel):
    kestra_execution_id: str
    patient_ref: str
    task_type: str
    contact: dict = Field(default_factory=dict)
    message: dict = Field(default_factory=dict)


class MessageSentRequest(BaseModel):
    event_id: str
    correlation_id: UUID
    event_type: str
    refs: dict


class InboundRequest(BaseModel):
    event_id: str
    event_type: str
    rc_room_id: str
    channel_conversation_id: str | int
    content: str
    occurred_at: str | None = None


class VideoRequest(BaseModel):
    correlation_id: UUID
    clinico_ref: str


class TriggerJourneyRequest(BaseModel):
    patient_ref: str
    task_type: str
    template_code: str = ""
    template_variables: dict = Field(default_factory=dict)
    contact_phone_e164: str = ""
    flow_id: str = "careplanner_jornada_basica"
    clinico_ref: str | None = None


@lru_cache(maxsize=1)
def get_service() -> CareplannerService:
    return build_careplanner_service()


def _ensure_signature(request_body: bytes, signature: str | None, service: CareplannerService) -> None:
    if not signature or not service._rc.verify_webhook_signature(request_body, signature):
        raise api_error(403, "invalid_signature", "Assinatura Rocket.Chat invalida")


@router.post("/tasks/open", status_code=status.HTTP_202_ACCEPTED)
async def open_task(
    body: OpenTaskRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    contact = body.contact or {}
    message = body.message or {}
    return await service.open_task(
        ctx,
        kestra_execution_id=body.kestra_execution_id,
        patient_ref=body.patient_ref,
        task_type=body.task_type,
        template_code=message.get("template_code", ""),
        template_variables=message.get("variables", {}),
        contact_phone=contact.get("phone_e164"),
        contact_role=contact.get("role", "PACIENTE"),
    )


@router.post("/events/message-sent", status_code=status.HTTP_200_OK)
async def message_sent_callback(
    request: Request,
    body: MessageSentRequest,
    x_rocketchat_signature: str | None = Header(default=None),
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    _ensure_signature(await request.body(), x_rocketchat_signature, service)
    return await service.process_message_sent(
        ctx,
        event_id=body.event_id,
        correlation_id=body.correlation_id,
        rc_room_id=body.refs["rc_room_id"],
        channel_conversation_id=body.refs["channel_conversation_id"],
    )


@router.post("/webhooks/rocketchat/inbound", status_code=status.HTTP_202_ACCEPTED)
async def rocketchat_inbound(
    request: Request,
    body: InboundRequest,
    x_rocketchat_signature: str | None = Header(default=None),
    service: CareplannerService = Depends(get_service),
) -> dict:
    _ensure_signature(await request.body(), x_rocketchat_signature, service)
    return await service.process_inbound_from_webhook(
        event_id=body.event_id,
        rc_room_id=body.rc_room_id,
        channel_conversation_id=body.channel_conversation_id,
        content=body.content,
        occurred_at=body.occurred_at,
    )


@router.post("/consultations/video", status_code=status.HTTP_201_CREATED)
async def open_video_session(
    body: VideoRequest,
    ctx: TenantContext = Depends(require_role("CLINICO")),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.open_video_session(
        ctx,
        correlation_id=body.correlation_id,
        clinico_ref=body.clinico_ref,
    )


@router.get("/consultations/video/{correlation_id}")
async def get_video_session(
    correlation_id: UUID,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.get_video_session_info(ctx, correlation_id)


@router.get("/tasks/{correlation_id}")
async def get_task(
    correlation_id: UUID,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.get_task_details(ctx, correlation_id)


@router.get("/tasks")
async def list_tasks(
    status_filter: str | None = None,
    page: int = 1,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.list_tasks(ctx, status_filter=status_filter, page=page)


@router.get("/dashboard/stats")
async def dashboard_stats(
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.get_dashboard_stats(ctx)


@router.post("/tasks/{correlation_id}/close", status_code=status.HTTP_200_OK)
async def close_task(
    correlation_id: UUID,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.close_task(ctx, correlation_id)


@router.post("/journeys/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_journey(
    body: TriggerJourneyRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Inicia uma nova jornada CarePlanner via Kestra.

    Requer role GESTOR ou CLINICO.
    Retorna o execution_id do Kestra e o correlation_id gerado pelo IntelliCare.
    """
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    return await service.trigger_journey(ctx, body)
