"""Modulo Gestor — ponto de entrada compativel com BaseModule."""
from __future__ import annotations

from fastapi import APIRouter

from intellicare_core.contracts.base import BaseModule, HealthResponse
from intellicare_core.db.session import tenant_session
from .router import router as gestor_router
from .migrations import GESTOR_MIGRATIONS


class Module(BaseModule):
    """Modulo de gestao da unidade de saude (TENANT_GESTOR)."""

    @property
    def name(self) -> str:
        return "gestor"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return gestor_router

    async def startup(self) -> None:
        from intellicare_core.db.session import get_engine
        from sqlalchemy import text
        
        # O startup de modulo do IntelliCare roda no schema public por definicao na inicializacao.
        # Os schemas tenant_ sao criados quando Tenants sao criados, entao aplicar as migracoes
        # para todos os tenants no startup.
        # Vamos abstrair e pegar todos os tenants para rodar as migracoes.
        async with get_engine().begin() as conn:
            tenants = (await conn.execute(text("SELECT slug FROM public.tenants"))).scalars().all()
            for slug in tenants:
                schema = f"tenant_{slug}"
                await conn.execute(text(f'SET search_path TO "{schema}"'))
                for sql in GESTOR_MIGRATIONS:
                    await conn.execute(text(sql))
            await conn.execute(text("SET search_path TO public"))

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
        )
