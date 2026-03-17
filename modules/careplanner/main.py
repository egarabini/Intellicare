"""Modulo CarePlanner — ponto de entrada compativel com BaseModule."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text

from intellicare_core.contracts.base import BaseModule, HealthResponse
from intellicare_core.db.session import get_engine

from .api.routes import router as careplanner_router
from .migrations import CAREPLANNER_MIGRATIONS

logger = logging.getLogger(__name__)


class Module(BaseModule):
    """Modulo CarePlanner Conversacional (DEM-038)."""

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

    async def shutdown(self) -> None:
        return None

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
            details={},
        )
