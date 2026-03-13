"""Modulo Financeiro — ponto de entrada compativel com BaseModule."""
from __future__ import annotations

from fastapi import APIRouter

from intellicare_core.contracts.base import BaseModule, HealthResponse
from .router import router as fin_router


class Module(BaseModule):
    """Modulo de contratos e faturamento (PLATFORM_ADMIN only)."""

    @property
    def name(self) -> str:
        return "financeiro"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return fin_router

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
        )

