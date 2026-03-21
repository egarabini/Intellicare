"""Módulo Oswaldo — Assistente de Prescrição Clínica."""
from __future__ import annotations

from fastapi import APIRouter
from intellicare_core.contracts.base import BaseModule, HealthResponse
from .api.routes import router as oswaldo_router

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

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
        )
