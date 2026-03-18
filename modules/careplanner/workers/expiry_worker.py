"""Worker de expiracao de jornadas do CarePlanner."""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import get_engine, tenant_session

from ..contracts import TaskStatus
from ..integrations import notify_task_expired
from ..repository import CareplannerRepository

logger = logging.getLogger(__name__)

SLA_DISPATCHED_HOURS = 24
SLA_SENT_HOURS = 72
CHECK_INTERVAL_SECS = 300


async def expiry_worker() -> None:
    logger.info("CarePlanner expiry worker iniciado")
    while True:
        try:
            await _expire_stale_tasks()
        except asyncio.CancelledError:
            logger.info("expiry_worker cancelado (shutdown)")
            break
        except Exception:
            logger.exception("erro no expiry_worker")
        await asyncio.sleep(CHECK_INTERVAL_SECS)


async def _expire_stale_tasks() -> None:
    repo = CareplannerRepository()
    async with get_engine().begin() as conn:
        tenants = (
            await conn.execute(text("SELECT slug FROM public.tenants WHERE status = 'active'"))
        ).scalars().all()

    for slug in tenants:
        ctx = TenantContext.from_slug(slug=slug, user_id="expiry-worker")
        try:
            await _expire_for_tenant(ctx, repo)
        except Exception:
            logger.exception("erro ao expirar jornadas do tenant %s", slug)


async def _expire_for_tenant(ctx: TenantContext, repo: CareplannerRepository) -> None:
    async with tenant_session(ctx) as db:
        rows = (
            await db.execute(
                text(
                    f"""
                    SELECT correlation_id, status, task_type, patient_ref
                    FROM care_tasks
                    WHERE (
                        (status = 'DISPATCHED' AND updated_at < NOW() - INTERVAL '{SLA_DISPATCHED_HOURS} hours')
                        OR
                        (status = 'SENT' AND updated_at < NOW() - INTERVAL '{SLA_SENT_HOURS} hours')
                    )
                    """
                )
            )
        ).mappings().all()

    for row in rows:
        try:
            await repo.transition_task_status(ctx, row["correlation_id"], TaskStatus.EXPIRED)
            await notify_task_expired(
                ctx=ctx,
                correlation_id=row["correlation_id"],
                task_type=row["task_type"],
                patient_ref=row["patient_ref"],
            )
            logger.info("task expirada: %s (era %s)", row["correlation_id"], row["status"])
        except ValueError:
            pass
