"""Dispatcher de tarefas CarePlanner (stub Fase B — retry implementado na Fase D)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def enqueue_dispatch(correlation_id: str, tenant_slug: str) -> None:
    """Stub da Fase B: o dispatch ocorre de forma sincronizada em services.open_task."""
    logger.debug("dispatcher.enqueue_dispatch: %s / %s (stub)", correlation_id, tenant_slug)
