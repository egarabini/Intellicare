"""Dispatcher assincrono do CarePlanner com retry e dead-letter via Redis."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from intellicare_core.contracts.base import TenantContext

from ..contracts import CareConversationUpsert, ParticipantRole, TaskStatus, Channel
from ..metrics import careplanner_dispatch_total
from ..repository import CareplannerRepository

logger = logging.getLogger(__name__)

QUEUE_KEY = "careplanner:dispatch:queue"
DEAD_KEY = "careplanner:dispatch:dead"
MAX_RETRIES = 3
BACKOFF_BASE = 0.5


async def enqueue_dispatch(correlation_id: str, tenant_slug: str) -> None:
    """Enfileira um dispatch no Redis."""
    try:
        from modules.notifications.redis_pubsub import get_redis

        redis = await get_redis()
        item = json.dumps(
            {
                "correlation_id": correlation_id,
                "tenant_slug": tenant_slug,
                "attempts": 0,
                "enqueued_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        await redis.rpush(QUEUE_KEY, item)
        logger.debug("dispatch enqueued: %s / %s", correlation_id, tenant_slug)
    except Exception:
        logger.warning("falha ao enfileirar dispatch", exc_info=True)


async def dispatcher_worker() -> None:
    from modules.notifications.redis_pubsub import get_redis

    logger.info("CarePlanner dispatcher worker iniciado")
    while True:
        try:
            redis = await get_redis()
            result = await redis.blpop(QUEUE_KEY, timeout=5)
            if result is None:
                continue
            _, raw = result
            item = json.loads(raw)
            await _do_dispatch(item)
        except asyncio.CancelledError:
            logger.info("dispatcher_worker cancelado (shutdown)")
            break
        except Exception:
            logger.exception("erro inesperado no dispatcher_worker loop")
            await asyncio.sleep(1)


async def _do_dispatch(item: dict) -> None:
    from modules.notifications.redis_pubsub import get_redis
    from ..services import build_careplanner_service

    correlation_id = item["correlation_id"]
    tenant_slug = item["tenant_slug"]
    attempts = item.get("attempts", 0)
    ctx = TenantContext.from_slug(slug=tenant_slug, user_id="dispatcher-worker")
    repo = CareplannerRepository()
    task = await repo.get_task(ctx, UUID(correlation_id))
    if task is None:
        logger.warning("dispatch: task nao encontrada %s", correlation_id)
        return
    if TaskStatus(task.status) not in {TaskStatus.CREATED, TaskStatus.DISPATCHED}:
        logger.debug("dispatch: task %s em status %s, ignorando", correlation_id, task.status)
        return

    metadata = task.metadata or {}
    last_error: Exception | None = None
    for attempt in range(attempts + 1, MAX_RETRIES + 1):
        try:
            svc = build_careplanner_service()
            channel = Channel(task.channel if hasattr(task, "channel") and task.channel else "rocketchat")
            rc_room_id = None
            if channel != Channel.WHATSAPP:
                rc_room_id = await svc._rc.ensure_room(tenant_slug, task.patient_ref)

            template = await repo.get_template_by_code(ctx, metadata.get("template_code", ""))
            
            raw_content = template.content if template else metadata.get("template_code", "")
            text_content = raw_content
            variables = metadata.get("template_variables", {})
            if variables and "{" in raw_content:
                for k, v in variables.items():
                    text_content = text_content.replace(f"{{{{{k}}}}}", str(v))
            
            await svc._send_to_channel(
                channel=channel, 
                rc_room_id=rc_room_id, 
                phone_e164=metadata.get("contact_phone"), 
                text=text_content
            )

            await repo.upsert_conversation(
                ctx,
                CareConversationUpsert(
                    correlation_id=UUID(correlation_id),
                    channel=channel,
                    channel_conversation_id=0,
                    rc_room_id=rc_room_id,
                    phone_e164=metadata.get("contact_phone"),
                    participant_role=ParticipantRole(metadata["contact_role"])
                    if metadata.get("contact_role")
                    else None,
                ),
            )
            await repo.transition_task_status(ctx, UUID(correlation_id), TaskStatus.DISPATCHED)
            careplanner_dispatch_total.labels(tenant_slug=tenant_slug, status="dispatched").inc()
            logger.info("dispatch ok: %s (tentativa %d)", correlation_id, attempt)
            return
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "dispatch falhou (%s), retry %d/%d em %.1fs: %s",
                    type(exc).__name__,
                    attempt,
                    MAX_RETRIES,
                    backoff,
                    correlation_id,
                )
                await asyncio.sleep(backoff)
                continue

    logger.error(
        "dispatch dead-letter apos %d tentativas: %s — %s",
        MAX_RETRIES,
        correlation_id,
        last_error,
    )
    careplanner_dispatch_total.labels(tenant_slug=tenant_slug, status="failed").inc()
    item["attempts"] = MAX_RETRIES
    item["failed_at"] = datetime.now(timezone.utc).isoformat()
    item["error"] = str(last_error) if last_error else "unknown"
    redis = await get_redis()
    await redis.rpush(DEAD_KEY, json.dumps(item))
    try:
        await repo.transition_task_status(ctx, UUID(correlation_id), TaskStatus.FAILED)
    except Exception:
        logger.warning("nao foi possivel marcar task como FAILED: %s", correlation_id, exc_info=True)
