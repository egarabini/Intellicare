"""Modelos para discovery e estado do orquestrador."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ModuleStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


@dataclass
class ModuleInfo:
    """Informacoes de um modulo descoberto."""

    name: str
    base_url: str
    version: str = ""
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    status: ModuleStatus = ModuleStatus.OFFLINE
    last_check: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "version": self.version,
            "description": self.description,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
        }


@dataclass
class RoutingDecision:
    """Decisao de roteamento do orquestrador."""

    target_modules: list[str]
    reason: str
    confidence: float = 1.0
    routing_method: str = "keyword"  # "llm" | "keyword" | "direct"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_modules": self.target_modules,
            "reason": self.reason,
            "confidence": self.confidence,
            "routing_method": self.routing_method,
        }


@dataclass
class ModuleResponse:
    """Resposta de um modulo chamado."""

    module_name: str
    endpoint: str
    status_code: int
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0

    @property
    def success(self) -> bool:
        return 200 <= self.status_code < 300 and not self.error

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "data": self.data,
            "error": self.error,
            "success": self.success,
            "duration_ms": round(self.duration_ms, 1),
        }


@dataclass
class AggregatedResponse:
    """Resultado da agregacao inteligente (EF-W004)."""

    synthesis: str                              # Main synthesized text
    key_points: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    critical_alerts: list[str] = field(default_factory=list)
    data_sources: dict[str, str] = field(default_factory=dict)   # {agent: "what it provided"}
    contradictions: list[dict] = field(default_factory=list)      # Contradiction objects
    aggregation_method: str = "simple"          # "llm" | "simple"
    recipient_type: str = "professional"        # "professional" | "patient"
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "synthesis": self.synthesis,
            "key_points": self.key_points,
            "recommended_actions": self.recommended_actions,
            "critical_alerts": self.critical_alerts,
            "data_sources": self.data_sources,
            "contradictions": self.contradictions,
            "aggregation_method": self.aggregation_method,
            "recipient_type": self.recipient_type,
            "confidence": self.confidence,
        }


@dataclass
class OrchestrationResult:
    """Resultado final da orquestracao."""

    query: str
    modules_used: list[str]
    responses: list[ModuleResponse]
    aggregated_response: str = ""
    routing_decision: RoutingDecision | None = None
    safety_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "modules_used": self.modules_used,
            "responses": [r.to_dict() for r in self.responses],
            "aggregated_response": self.aggregated_response,
            "routing": self.routing_decision.to_dict() if self.routing_decision else None,
            "safety_warnings": self.safety_warnings,
        }
