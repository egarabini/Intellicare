"""Modelos de dados do Florence."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from florence.engine.rag.models import RAGResult


class InterpretationLevel(str, Enum):
    """Nivel de interpretacao do resultado."""

    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"
    PANIC = "panic"


class ClinicalSignificance(str, Enum):
    """Significancia clinica do achado."""

    ROUTINE = "routine"
    ATTENTION = "attention"
    URGENT = "urgent"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Direcao da tendencia."""

    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class ReferenceRange:
    """Faixa de referencia para um exame."""

    lab_id: str
    name: str
    loinc_code: str
    unit: str
    normal_min: float | None
    normal_max: float | None
    low_min: float | None = None
    high_max: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    panic_low: float | None = None
    panic_high: float | None = None
    gender_specific: bool = False
    age_specific: bool = False


@dataclass
class LabInterpretation:
    """Interpretacao de um resultado laboratorial."""

    lab_id: str
    lab_name: str
    loinc_code: str
    value: float
    unit: str
    level: InterpretationLevel
    reference_range: str
    message: str
    significance: ClinicalSignificance
    timestamp: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lab_id": self.lab_id,
            "lab_name": self.lab_name,
            "loinc_code": self.loinc_code,
            "value": self.value,
            "unit": self.unit,
            "level": self.level.value,
            "reference_range": self.reference_range,
            "message": self.message,
            "significance": self.significance.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class TrendAnalysis:
    """Resultado de analise de tendencia."""

    lab_id: str
    lab_name: str
    direction: TrendDirection
    slope: float | None
    current_value: float
    previous_value: float | None
    change_percent: float | None
    period_days: int
    data_points: int
    values: list[float] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "lab_id": self.lab_id,
            "lab_name": self.lab_name,
            "direction": self.direction.value,
            "slope": self.slope,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_percent": self.change_percent,
            "period_days": self.period_days,
            "data_points": self.data_points,
            "message": self.message,
        }


@dataclass
class CorrelationFinding:
    """Achado de correlacao entre exames."""

    pattern_id: str
    pattern_name: str
    description: str
    labs_involved: list[str]
    significance: ClinicalSignificance
    message: str
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_name": self.pattern_name,
            "description": self.description,
            "labs_involved": self.labs_involved,
            "significance": self.significance.value,
            "message": self.message,
            "recommendations": self.recommendations,
        }


@dataclass
class ClinicalAnalysis:
    """Resultado completo de analise clinica."""

    patient_id: str
    interpretations: list[LabInterpretation]
    trends: list[TrendAnalysis]
    correlations: list[CorrelationFinding]
    summary: str
    significance: ClinicalSignificance
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "interpretations": [i.to_dict() for i in self.interpretations],
            "trends": [t.to_dict() for t in self.trends],
            "correlations": [c.to_dict() for c in self.correlations],
            "summary": self.summary,
            "significance": self.significance.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ClinicalAnalysisWithRAG(ClinicalAnalysis):
    """Análise clínica com protocolos RAG relevantes."""

    relevant_protocols: list[Any] = field(default_factory=list)  # list[RAGResult]
    rag_query: str | None = None
    rag_execution_time_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "relevant_protocols": [
                {
                    "protocol_id": p.protocol_id,
                    "title": p.title,
                    "content": p.content,
                    "score": p.score,
                    "metadata": p.metadata,
                }
                for p in self.relevant_protocols
            ],
            "rag_query": self.rag_query,
            "rag_execution_time_ms": self.rag_execution_time_ms,
        })
        return base_dict
