"""ESC/ESH Staging Strategy — Hipertensao Arterial (ESC/ESH 2018)."""

from datetime import datetime
from typing import Any

from oswaldo.engine.models import SeverityLevel, StagingResult
from oswaldo.engine.staging.base import StagingStrategy


class ESCESHStagingStrategy(StagingStrategy):
    """Estrategia de estadiamento ESC/ESH para HAS baseado em PA."""

    def calculate_stage(self, observations: dict[str, Any]) -> StagingResult:
        systolic = observations.get("systolic_bp")
        diastolic = observations.get("diastolic_bp")
        stage, label, severity = self._calculate_bp_stage(systolic, diastolic)
        axes = {"bp_category": stage} if stage != "UNKNOWN" else {}

        return StagingResult(
            disease_id=self.profile.id,
            stage=stage,
            stage_label=label,
            severity=severity,
            axes=axes,
            timestamp=datetime.now(),
            observations_used=observations,
        )

    def _calculate_bp_stage(
        self, systolic: float | None, diastolic: float | None
    ) -> tuple[str, str, SeverityLevel]:
        if systolic is None or diastolic is None:
            return ("UNKNOWN", "Unknown", SeverityLevel.INFO)
        if systolic >= 180 or diastolic >= 110:
            return ("GRADE3", "Hipertensao Grau 3", SeverityLevel.CRITICAL)
        if (160 <= systolic < 180) or (100 <= diastolic < 110):
            return ("GRADE2", "Hipertensao Grau 2", SeverityLevel.CRITICAL)
        if (140 <= systolic < 160) or (90 <= diastolic < 100):
            return ("GRADE1", "Hipertensao Grau 1", SeverityLevel.WARNING)
        if (130 <= systolic < 140) or (85 <= diastolic < 90):
            return ("HIGH_NORMAL", "Pressao Normal-Alta", SeverityLevel.WARNING)
        if (120 <= systolic < 130) or (80 <= diastolic < 85):
            return ("NORMAL", "Pressao Normal", SeverityLevel.INFO)
        if systolic < 120 and diastolic < 80:
            return ("OPTIMAL", "Pressao Otima", SeverityLevel.INFO)
        return ("UNKNOWN", "Unknown", SeverityLevel.INFO)
