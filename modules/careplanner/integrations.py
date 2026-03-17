"""Integracoes internas do CarePlanner com outros modulos IntelliCare."""
from __future__ import annotations

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
        from modules.notifications.redis_pubsub import publish_broadcast, publish_notification

        payload = {
            "type": "message",
            "priority": "high",
            "title": "Paciente respondeu",
            "body": f'{patient_ref} respondeu à jornada {task_type}: "{content[:80]}"',
            "data": {
                "correlation_id": str(correlation_id),
                "task_type": task_type,
                "patient_ref": patient_ref,
                "module": "careplanner",
                "event": "REPLIED",
            },
        }
        if clinico_ref:
            await publish_notification(ctx.tenant_id, clinico_ref, payload)
        else:
            await publish_broadcast(ctx.tenant_id, payload)
        logger.info(
            "Notificacao REPLIED enviada: tenant=%s correlation=%s clinico=%s",
            ctx.tenant_id,
            correlation_id,
            clinico_ref,
        )
    except Exception:
        logger.warning(
            "Falha ao notificar CLINICO (non-fatal): correlation=%s",
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
