"""TrendAlertRule — alertas baseados em tendencias temporais."""

import uuid
from datetime import datetime, timezone
from typing import Any

from oswaldo.engine.alerts.base import AlertRule
from oswaldo.engine.models import Alert, SeverityLevel, StagingResult, TrendDirection, TrendResult


class TrendAlertRule(AlertRule):
    """Regra de alerta baseada em tendencia temporal."""

    def evaluate(
        self,
        patient_id: str,
        disease_id: str,
        observations: dict[str, Any],
        staging: StagingResult | None = None,
        trends: dict[str, TrendResult] | None = None,
    ) -> Alert | None:
        if not trends:
            return None
        trend = trends.get(self.config.observation_id)
        if not trend:
            return None
        if trend.direction == TrendDirection.INSUFFICIENT_DATA:
            return None

        threshold_per_day = float(self.config.threshold) / 365.0
        if not self._check_condition(trend.slope, self.config.condition, threshold_per_day):
            return None

        severity = _map_severity(self.config.severity)
        annual_change = trend.slope * 365.0

        return Alert(
            alert_id=f"alert-{uuid.uuid4()}",
            disease_id=disease_id,
            alert_type="trend",
            severity=severity,
            message=self.config.message,
            observation_id=self.config.observation_id,
            current_value=trend.current_value,
            threshold_value=float(self.config.threshold),
            timestamp=datetime.now(timezone.utc),
            metadata={
                "trend_direction": trend.direction.value,
                "slope_per_day": trend.slope,
                "annual_change": annual_change,
                "change_percent": trend.change_percent,
                "alert_config_id": self.config.id,
            },
        )


def _map_severity(severity_str: str) -> SeverityLevel:
    return {
        "info": SeverityLevel.INFO,
        "warning": SeverityLevel.WARNING,
        "critical": SeverityLevel.CRITICAL,
    }.get(severity_str.lower(), SeverityLevel.INFO)
