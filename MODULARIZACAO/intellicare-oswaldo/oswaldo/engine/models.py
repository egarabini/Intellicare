"""Modelos de dados do Oswaldo."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SeverityLevel(str, Enum):
    """Nivel de severidade."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Direcao de tendencia."""

    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class StagingResult:
    """Resultado de estadiamento clinico."""

    disease_id: str
    stage: str
    stage_label: str
    severity: SeverityLevel
    axes: dict[str, str]
    timestamp: datetime
    observations_used: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "disease_id": self.disease_id,
            "stage": self.stage,
            "stage_label": self.stage_label,
            "severity": self.severity.value,
            "axes": self.axes,
            "timestamp": self.timestamp.isoformat(),
            "observations_used": self.observations_used,
        }


@dataclass
class TrendResult:
    """Resultado de analise de tendencia."""

    observation_id: str
    direction: TrendDirection
    slope: float | None
    current_value: float | None
    previous_value: float | None
    change_percent: float | None
    period_days: int
    data_points: int
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "direction": self.direction.value,
            "slope": self.slope,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_percent": self.change_percent,
            "period_days": self.period_days,
            "data_points": self.data_points,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Alert:
    """Alerta gerado pelo sistema."""

    alert_id: str
    disease_id: str
    alert_type: str
    severity: SeverityLevel
    message: str
    observation_id: str | None
    current_value: Any | None
    threshold_value: Any | None
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "disease_id": self.disease_id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "message": self.message,
            "observation_id": self.observation_id,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class OswaldoPatientSummary:
    """Resumo completo do paciente para doencas cronicas."""

    patient_id: str
    diseases: list[str]
    staging_results: dict[str, StagingResult]
    trend_results: dict[str, TrendResult]
    alerts: list[Alert]
    last_updated: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "diseases": self.diseases,
            "staging_results": {k: v.to_dict() for k, v in self.staging_results.items()},
            "trend_results": {k: v.to_dict() for k, v in self.trend_results.items()},
            "alerts": [a.to_dict() for a in self.alerts],
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
        }
