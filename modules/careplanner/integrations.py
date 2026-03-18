"""Integracoes internas do CarePlanner com outros modulos IntelliCare."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from uuid import UUID

from intellicare_core.contracts.base import TenantContext

logger = logging.getLogger(__name__)


async def notify_clinico_replied(
    ctx: TenantContext,
    correlation_id: UUID,
    task_type: str,
    patient_ref: str,
    clinico_ref: str | None,
    content: str,
) -> None:
    try:
        from modules.notifications.redis_pubsub import publish_broadcast
        from modules.notifications.schemas import NotificationCreate
        from modules.notifications.service import NotificationService

        notif_data = {
            "module": "careplanner",
            "event": "REPLIED",
            "correlation_id": str(correlation_id),
            "task_type": task_type,
            "patient_ref": patient_ref,
        }
        title = "Paciente respondeu"
        body = f'{patient_ref} respondeu à jornada {task_type}: "{content[:80]}"'

        if clinico_ref:
            svc = NotificationService()
            await svc.send(
                ctx,
                NotificationCreate(
                    user_id=clinico_ref,
                    type="message",
                    priority="high",
                    title=title,
                    body=body,
                    data=notif_data,
                ),
            )

        broadcast_payload = {
            "type": "message",
            "priority": "high",
            "title": title,
            "body": body,
            "data": notif_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await publish_broadcast(ctx.tenant_id, broadcast_payload)
        logger.info(
            "Notificacao REPLIED enviada: tenant=%s correlation=%s clinico=%s",
            ctx.tenant_id,
            correlation_id,
            clinico_ref,
        )
    except Exception:
        logger.warning(
            "Falha ao notificar REPLIED (non-fatal): correlation=%s",
            correlation_id,
            exc_info=True,
        )


async def notify_task_expired(
    ctx: TenantContext,
    correlation_id: UUID,
    task_type: str,
    patient_ref: str,
) -> None:
    try:
        from modules.notifications.redis_pubsub import publish_broadcast

        payload = {
            "type": "alert",
            "priority": "normal",
            "title": "Jornada expirada sem resposta",
            "body": f"Jornada {task_type} de {patient_ref} expirou sem resposta do paciente.",
            "data": {
                "module": "careplanner",
                "event": "EXPIRED",
                "correlation_id": str(correlation_id),
                "task_type": task_type,
                "patient_ref": patient_ref,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await publish_broadcast(ctx.tenant_id, payload)
        logger.info(
            "Notificacao EXPIRED enviada: tenant=%s correlation=%s",
            ctx.tenant_id,
            correlation_id,
        )
    except Exception:
        logger.warning(
            "Falha ao notificar EXPIRED (non-fatal): correlation=%s",
            correlation_id,
            exc_info=True,
        )


async def trigger_cuidado_encounter(
    ctx: TenantContext,
    correlation_id: UUID,
    task_type: str,
    patient_ref: str,
) -> None:
    try:
        from modules.notifications.redis_pubsub import get_redis

        redis = await get_redis()
        channel = f"careplanner:{ctx.tenant_id}:replied"
        payload = json.dumps(
            {
                "event": "REPLIED",
                "correlation_id": str(correlation_id),
                "task_type": task_type,
                "patient_ref": patient_ref,
                "tenant_id": ctx.tenant_id,
            }
        )
        await redis.publish(channel, payload)
        logger.info(
            "Evento REPLIED publicado no Redis: tenant=%s correlation=%s",
            ctx.tenant_id,
            correlation_id,
        )
    except Exception:
        logger.warning(
            "Falha ao publicar evento cuidado (non-fatal): correlation=%s",
            correlation_id,
            exc_info=True,
        )
