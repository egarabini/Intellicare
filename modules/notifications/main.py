"""Modulo Notifications — ponto de entrada compativel com BaseModule."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text

from intellicare_core.contracts.base import BaseModule, HealthResponse
from intellicare_core.db.session import get_engine

from .migrations import NOTIFICATION_MIGRATIONS
from .redis_pubsub import close_redis, get_redis
from .router import router as notification_router

logger = logging.getLogger(__name__)


class Module(BaseModule):
    """Modulo de notificacoes em tempo real (DEM-026)."""

    @property
    def name(self) -> str:
        return "notifications"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return notification_router

    async def startup(self) -> None:
        """Executa migracoes de notificacoes em todos os tenants."""
        # Verificar conexao Redis
        try:
            r = await get_redis()
            await r.ping()
            logger.info("Redis conectado para notificacoes.")
        except Exception:
            logger.warning("Redis indisponivel — notificacoes em tempo real desabilitadas.")

        # Migracoes por tenant
        async with get_engine().begin() as conn:
            tenants = (
                await conn.execute(text("SELECT slug FROM public.tenants"))
            ).scalars().all()

            for slug in tenants:
                schema = f"tenant_{slug}"
                try:
                    await conn.execute(text(f'SET search_path TO "{schema}"'))
                    for sql in NOTIFICATION_MIGRATIONS:
                        await conn.execute(text(sql))
                    logger.info("Migracoes notifications aplicadas: %s", schema)
                except Exception:
                    logger.exception("Erro ao migrar notifications para %s", schema)

            await conn.execute(text("SET search_path TO public"))

    async def shutdown(self) -> None:
        """Fecha recursos (Redis)."""
        await close_redis()

    async def health(self) -> HealthResponse:
        details = {}
        try:
            r = await get_redis()
            await r.ping()
            details["redis"] = "connected"
        except Exception:
            details["redis"] = "disconnected"

        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
            details=details,
        )
