"""Modulo CarePlanner — ponto de entrada compativel com BaseModule."""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter
from sqlalchemy import text

from intellicare_core.contracts.base import BaseModule, HealthResponse
from intellicare_core.db.session import get_engine

from .api.routes import router as careplanner_router
from .migrations import CAREPLANNER_MIGRATIONS
from .workers.dispatcher import dispatcher_worker
from .workers.expiry_worker import expiry_worker

logger = logging.getLogger(__name__)


class Module(BaseModule):
    """Modulo CarePlanner Conversacional (DEM-038)."""

    def __init__(self) -> None:
        self._dispatcher_task: asyncio.Task | None = None
        self._expiry_task: asyncio.Task | None = None

    @property
    def name(self) -> str:
        return "careplanner"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return careplanner_router

    async def startup(self) -> None:
        async with get_engine().begin() as conn:
            tenants = (await conn.execute(text("SELECT slug FROM public.tenants"))).scalars().all()
            for slug in tenants:
                schema = f"tenant_{slug}"
                try:
                    await conn.execute(text(f'SET search_path TO "{schema}"'))
                    for sql in CAREPLANNER_MIGRATIONS:
                        await conn.execute(text(sql))
                    logger.info("Migrations careplanner aplicadas: %s", schema)
                except Exception:
                    logger.exception("Erro ao migrar careplanner para %s", schema)
            await conn.execute(text("SET search_path TO public"))
            
        from .services import build_careplanner_service
        from intellicare_core.contracts.base import TenantContext
        
        svc = build_careplanner_service()
        for slug in tenants:
            ctx = TenantContext.from_slug(slug=slug, user_id="startup-seed")
            await svc.seed_default_templates(ctx)

        self._dispatcher_task = asyncio.create_task(dispatcher_worker())
        self._expiry_task = asyncio.create_task(expiry_worker())
        logger.info("CarePlanner workers agendados.")

    async def shutdown(self) -> None:
        for task in [self._dispatcher_task, self._expiry_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
            details={},
        )
