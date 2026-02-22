"""Schema de informacao do modulo — resposta de GET /api/v1/info."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModuleInfo(BaseModel):
    """Informacoes publicas de um modulo IntelliCare.

    Todo modulo DEVE retornar este schema em GET /api/v1/info.
    Usado por Wanda para descoberta dinamica de capabilities.
    """

    name: str = Field(..., description="Nome do modulo (ex: intellicare-oswaldo)")
    version: str = Field(..., description="Versao SemVer (ex: 1.0.0)")
    status: str = Field(
        default="healthy",
        description="Estado atual: healthy | degraded | unhealthy",
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Lista de capabilities (ex: chronic-disease-monitoring, staging)",
    )
    fhir_version: str = Field(default="R4", description="Versao FHIR suportada")
    description: str = Field(default="", description="Descricao curta do modulo")
    metadata: dict[str, object] = Field(
        default_factory=dict,
        description="Dados extras especificos do modulo",
    )
