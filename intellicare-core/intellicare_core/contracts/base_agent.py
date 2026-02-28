"""Interface base que todo agente IntelliCare deve implementar."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from intellicare_core.contracts.health import HealthCheck
from intellicare_core.contracts.module_info import ModuleInfo


class AnalysisRequest(BaseModel):
    """Request padrao para analise de um agente."""

    patient_id: str = Field(..., description="ID FHIR do paciente")
    query: str = Field(default="", description="Consulta em linguagem natural")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parametros especificos do agente",
    )


class AnalysisResponse(BaseModel):
    """Response padrao de analise de um agente."""

    success: bool = True
    patient_id: str = ""
    analysis: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = Field(default="", description="Nome do agente que gerou a resposta")


class BaseAgent(ABC):
    """Interface que todo agente IntelliCare deve implementar.

    Garante que todos os modulos expoe os mesmos endpoints padrao:
    - get_info() -> ModuleInfo (para /api/v1/info)
    - get_health() -> HealthCheck (para /api/v1/health)
    - analyze() -> AnalysisResponse (para /api/v1/analyze)
    """

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description

    @abstractmethod
    def get_info(self) -> ModuleInfo:
        """Retorna informacoes do modulo (GET /api/v1/info)."""
        ...

    @abstractmethod
    def get_health(self) -> HealthCheck:
        """Retorna status de saude do modulo (GET /api/v1/health)."""
        ...

    @abstractmethod
    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Executa analise principal do agente (POST /api/v1/analyze)."""
        ...
