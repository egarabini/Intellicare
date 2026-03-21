"""Rotas FastAPI do modulo CarePlanner."""
from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from intellicare_core.auth.jwt import get_current_tenant, require_role
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error

from ..contracts import Channel
from ..services import CareplannerService, build_careplanner_service

router = APIRouter()


class OpenTaskRequest(BaseModel):
    kestra_execution_id: str
    patient_ref: str
    task_type: str
    contact: dict = Field(default_factory=dict)
    message: dict = Field(default_factory=dict)
    appointment_id: str | None = None


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
    template_code: str | None = None
    template_variables: dict = Field(default_factory=dict)
    contact_phone_e164: str | None = None
    contact_email: str | None = None
    channel: Channel = Channel.ROCKETCHAT
    flow_id: str = "careplanner_jornada_com_fallback"
    clinico_ref: str | None = None
    appointment_id: str | None = None


class TemplateCreateRequest(BaseModel):
    template_code: str = Field(..., pattern=r"^[a-z0-9_]{2,64}$",
                               description="snake_case, 2-64 chars")
    channel: str = "rocketchat"
    content: str = Field(..., min_length=1, max_length=2000)
    variables: list[str] = Field(default_factory=list)
    active: bool = True


class TemplateUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    variables: list[str] = Field(default_factory=list)
    active: bool = True


@lru_cache(maxsize=1)
def get_service() -> CareplannerService:
    return build_careplanner_service()


def _ensure_signature(request_body: bytes, signature: str | None, service: CareplannerService) -> None:
    if not signature or not service._rc.verify_webhook_signature(request_body, signature):
        raise api_error(403, "invalid_signature", "Assinatura Rocket.Chat invalida")


@router.get("/health/adapters", status_code=200)
async def adapters_health(
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Retorna status de conectividade de cada adapter de canal."""
    return await service.health_check_adapters()


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
        contact_email=contact.get("contact_email"),
        contact_role=contact.get("role", "PACIENTE"),
        appointment_id=body.appointment_id,
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


@router.post("/webhook/whatsapp/{token}", status_code=status.HTTP_200_OK)
async def whatsapp_webhook(
    token: str,
    request: Request,
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Recebe eventos inbound do WhatsApp via Evolution API."""
    body = await request.json()

    # Verificar token de segurança
    from ..config import get_careplanner_settings
    from ..adapters.whatsapp import WhatsAppAdapter
    settings = get_careplanner_settings()
    wa = WhatsAppAdapter(settings)
    if not wa.verify_webhook_secret(token):
        raise api_error(401, "unauthorized", "Token invalido")

    # Processar apenas eventos de mensagem recebida
    event = body.get("event", "")
    if event != "messages.upsert":
        return {"status": "ignored", "event": event}

    data = body.get("data", {})
    key = data.get("key", {})

    # Ignorar mensagens enviadas pelo bot (fromMe=True)
    if key.get("fromMe", False):
        return {"status": "ignored", "reason": "fromMe"}

    remote_jid = key.get("remoteJid", "")
    phone = wa.extract_phone_from_jid(remote_jid)
    message_obj = data.get("message", {})
    text = (
        message_obj.get("conversation")
        or message_obj.get("extendedTextMessage", {}).get("text")
        or ""
    )

    if not phone or not text:
        return {"status": "ignored", "reason": "sem phone ou texto"}

    # Processar como inbound — mesmo handler do RC
    # O service.handle_whatsapp_inbound busca care_conversation pelo phone_e164
    normalized_response = wa.normalize_confirmation(text)
    await service.handle_whatsapp_inbound(
        phone=phone,
        text=text,
        normalized_response=normalized_response,
    )
    return {"status": "ok"}


@router.post("/webhook/sms/{token}", status_code=status.HTTP_200_OK)
async def sms_webhook(
    token: str,
    request: Request,
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Recebe respostas SMS via Jasmin MO webhook."""
    from ..config import get_careplanner_settings
    from ..adapters.sms import SMSAdapter
    settings = get_careplanner_settings()
    sms = SMSAdapter(settings)
    if not sms.verify_webhook_secret(token):
        raise api_error(401, "unauthorized", "Token invalido")

    body = await request.json()
    phone_raw = body.get("from", "")
    text = body.get("content", "")

    if not phone_raw or not text:
        return {"status": "ignored", "reason": "sem phone ou texto"}

    phone_e164 = f"+{phone_raw.lstrip('+')}"
    await service.handle_whatsapp_inbound(phone=phone_e164.lstrip("+"), text=text)
    return {"status": "ok"}


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
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    return await service.get_video_session_info(ctx, correlation_id)


@router.get("/journeys/{correlation_id}/report.pdf")
async def journey_report_pdf(
    correlation_id: UUID,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
):
    """Exporta jornada CarePlanner como PDF."""
    pdf_bytes = await service.generate_journey_report(ctx, correlation_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=jornada_{correlation_id}.pdf"
        },
    )


@router.get("/tasks/{correlation_id}")
async def get_task(
    correlation_id: UUID,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    return await service.get_task_details(ctx, correlation_id)


@router.get("/tasks")
async def list_tasks(
    status_filter: str | None = None,
    page: int = 1,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    return await service.list_tasks(ctx, status_filter=status_filter, page=page)


@router.get("/dashboard/stats")
async def dashboard_stats(
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.get_dashboard_stats(ctx)


@router.get("/appointments/{appointment_id}/journey")
async def get_journey_by_appointment(
    appointment_id: UUID,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Retorna a jornada CarePlanner ativa vinculada a um agendamento."""
    if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
        raise api_error(403, "forbidden", "Role 'GESTOR' ou 'CLINICO' necessaria")
    task = await service.repo.get_task_by_appointment(ctx, appointment_id)
    if not task:
        raise api_error(404, "not_found", "Nenhuma jornada ativa para este agendamento")
    return task.model_dump(mode="json")


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


@router.get("/templates")
async def list_templates_route(
    active: bool | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    items = await service.list_templates(ctx, active_only=bool(active))
    return {"items": items}


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreateRequest,
    ctx: TenantContext = Depends(require_role("GESTOR")),
    service: CareplannerService = Depends(get_service),
) -> dict:
    from ..contracts import CareTemplateCreate, Channel
    payload = CareTemplateCreate(
        template_code=body.template_code,
        channel=Channel(body.channel),
        content=body.content,
        variables=body.variables,
        active=body.active,
    )
    return await service.create_template_record(ctx, payload)


@router.put("/templates/{template_id}")
async def update_template(
    template_id: UUID,
    body: TemplateUpdateRequest,
    ctx: TenantContext = Depends(require_role("GESTOR")),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.update_template_record(
        ctx, template_id, body.content, body.variables, body.active
    )


@router.patch("/templates/{template_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_template(
    template_id: UUID,
    ctx: TenantContext = Depends(require_role("GESTOR")),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.toggle_template(ctx, template_id)
