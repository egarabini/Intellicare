"""Módulo Oswaldo — Assistente de Prescrição Clínica."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text

from intellicare_core.contracts.base import BaseModule, HealthResponse
from intellicare_core.db.session import get_engine

from .api.routes import router as oswaldo_router
from .migrations import OSWALDO_PUBLIC_MIGRATIONS, OSWALDO_TENANT_MIGRATIONS

logger = logging.getLogger(__name__)

class Module(BaseModule):
    """Módulo base Oswaldo (Prescrições Estruturadas e sugestão ágil de CID-10)."""

    @property
    def name(self) -> str:
        return "oswaldo"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return oswaldo_router

    async def startup(self) -> None:
        async with get_engine().begin() as conn:
            for sql in OSWALDO_PUBLIC_MIGRATIONS:
                await conn.execute(text(sql))

            tenants = (await conn.execute(text("SELECT slug FROM public.tenants"))).scalars().all()
            for slug in tenants:
                schema = f"tenant_{slug}"
                try:
                    await conn.execute(text(f'SET search_path TO "{schema}", public'))
                    for sql in OSWALDO_TENANT_MIGRATIONS:
                        await conn.execute(text(sql))
                    logger.info("Migracoes Oswaldo aplicadas: %s", schema)
                except Exception:
                    logger.exception("Erro ao migrar Oswaldo para %s", schema)
            await conn.execute(text("SET search_path TO public"))

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
        )
