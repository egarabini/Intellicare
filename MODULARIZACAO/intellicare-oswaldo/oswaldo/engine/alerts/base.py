"""AlertRule — interface abstrata para regras de alerta."""

from abc import ABC, abstractmethod
from typing import Any

from oswaldo.engine.models import Alert, StagingResult, TrendResult
from oswaldo.profiles.models import AlertConfig


class AlertRule(ABC):
    """Interface abstrata para regras de alerta."""

    def __init__(self, config: AlertConfig) -> None:
        self.config = config

    @abstractmethod
    def evaluate(
        self,
        patient_id: str,
        disease_id: str,
        observations: dict[str, Any],
        staging: StagingResult | None = None,
        trends: dict[str, TrendResult] | None = None,
    ) -> Alert | None:
        """Avalia se alerta deve ser gerado."""

    def _get_observation_value(self, observations: dict[str, Any], observation_id: str) -> float | None:
        value = observations.get(observation_id)
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict) and "value" in value:
            return float(value["value"])
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        if condition == "gt":
            return value > threshold
        if condition == "gte":
            return value >= threshold
        if condition == "lt":
            return value < threshold
        if condition == "lte":
            return value <= threshold
        if condition == "eq":
            return value == threshold
        raise ValueError(f"Condicao desconhecida: {condition}")
