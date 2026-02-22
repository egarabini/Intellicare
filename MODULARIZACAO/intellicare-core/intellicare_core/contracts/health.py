"""Schema de health check — resposta de GET /api/v1/health."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class DependencyStatus(BaseModel):
    """Status de uma dependencia (database, fhir server, redis, etc.)."""

    name: str
    status: str = Field(description="connected | disconnected | degraded")
    latency_ms: float | None = None
    details: str = ""


class HealthCheck(BaseModel):
    """Resposta padrao de health check para modulos IntelliCare.

    Todo modulo DEVE retornar este schema em GET /api/v1/health.
    """

    status: str = Field(
        default="healthy",
        description="Estado geral: healthy | degraded | unhealthy",
    )
    module_name: str = Field(default="", description="Nome do modulo")
    version: str = Field(default="", description="Versao do modulo")
    uptime_seconds: float = Field(default=0.0, description="Tempo ativo em segundos")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dependencies: list[DependencyStatus] = Field(
        default_factory=list,
        description="Status de cada dependencia",
    )

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"
