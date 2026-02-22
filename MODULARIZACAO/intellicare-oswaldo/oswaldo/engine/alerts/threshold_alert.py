"""ThresholdAlertRule — alertas baseados em thresholds de valores."""

import uuid
from datetime import datetime, timezone
from typing import Any

from oswaldo.engine.alerts.base import AlertRule
from oswaldo.engine.models import Alert, SeverityLevel, StagingResult, TrendResult


class ThresholdAlertRule(AlertRule):
    """Regra de alerta baseada em threshold de valor."""

    def evaluate(
        self,
        patient_id: str,
        disease_id: str,
        observations: dict[str, Any],
        staging: StagingResult | None = None,
        trends: dict[str, TrendResult] | None = None,
    ) -> Alert | None:
        value = self._get_observation_value(observations, self.config.observation_id)
        if value is None:
            return None

        threshold = float(self.config.threshold)
        if not self._check_condition(value, self.config.condition, threshold):
            return None

        severity = _map_severity(self.config.severity)
        return Alert(
            alert_id=f"alert-{uuid.uuid4()}",
            disease_id=disease_id,
            alert_type="threshold",
            severity=severity,
            message=self.config.message,
            observation_id=self.config.observation_id,
            current_value=value,
            threshold_value=threshold,
            timestamp=datetime.now(timezone.utc),
            metadata={"condition": self.config.condition, "alert_config_id": self.config.id},
        )


def _map_severity(severity_str: str) -> SeverityLevel:
    return {
        "info": SeverityLevel.INFO,
        "warning": SeverityLevel.WARNING,
        "critical": SeverityLevel.CRITICAL,
    }.get(severity_str.lower(), SeverityLevel.INFO)
