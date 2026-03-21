"""Modulo Florence — Assistente de Documentação Clínica."""
from __future__ import annotations

from fastapi import APIRouter
from intellicare_core.contracts.base import BaseModule, HealthResponse
from .api.routes import router as florence_router

class Module(BaseModule):
    """Módulo base Florence (Anotações Clínicas SOAP e Livres)."""

    @property
    def name(self) -> str:
        return "florence"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return florence_router

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
        )
