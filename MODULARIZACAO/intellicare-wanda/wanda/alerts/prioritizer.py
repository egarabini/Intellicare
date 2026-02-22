"""Alert prioritizer — calculates priority score 0-100 with context factors (EF-W007)."""

from __future__ import annotations

import logging
from typing import Optional

from wanda.alerts.models import AlertPriority, ClinicalAlert

logger = logging.getLogger(__name__)

_BASE_SCORES: dict[str, int] = {
    "critical": 90,
    "high": 70,
    "medium": 50,
    "low": 25,
}

_SEVERITY_LEVELS = ["low", "medium", "high", "critical"]


class AlertPrioritizer:
    """Calculates context-aware priority for clinical alerts.

    Base score comes from severity. Contextual factors can increase or decrease it:
    - +10: patient currently hospitalized
    - +10: first alert of this type for patient today
    - +10: worsening trend (multiple alerts in last 2h)
    - +5:  high-risk patient flag in clinical_data
    - -10: alert type has been recurring for >7 days without resolution
    """

    async def calculate_priority(
        self,
        alert: ClinicalAlert,
        patient_context: Optional[dict] = None,
    ) -> AlertPriority:
        """Calculate final priority score and potentially upgrade severity."""
        base = _BASE_SCORES.get(alert.severity, 50)
        score = base
        factors: list[str] = []
        severity = alert.severity

        ctx = patient_context or {}
        clinical = alert.clinical_data

        if ctx.get("hospitalized") or clinical.get("hospitalized"):
            score += 10
            factors.append("paciente internado")

        if clinical.get("first_occurrence", False):
            score += 10
            factors.append("primeiro alerta deste tipo")

        if clinical.get("worsening_trend", False):
            score += 10
            factors.append("tendencia de piora")

        if ctx.get("high_risk") or clinical.get("high_risk"):
            score += 5
            factors.append("paciente de alto risco")

        if clinical.get("recurring_unresolved", False):
            score -= 10
            factors.append("alerta recorrente sem resolucao")

        # Upgrade severity if score pushed past threshold
        score = max(0, min(100, score))
        idx = _SEVERITY_LEVELS.index(severity)
        if score >= 85 and severity != "critical":
            severity = "critical"
            factors.append("severidade escalada para critica")
        elif score >= 65 and idx < _SEVERITY_LEVELS.index("high"):
            severity = "high"
            factors.append("severidade escalada para alta")

        logger.debug(
            "Alert %s priority: score=%d severity=%s factors=%s",
            alert.alert_id, score, severity, factors,
        )
        return AlertPriority(score=score, adjusted_severity=severity, factors=factors)
