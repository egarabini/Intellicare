"""ADA Staging Strategy — Diabetes Mellitus Tipo 2 (ADA 2024)."""

from datetime import datetime
from typing import Any

from oswaldo.engine.models import SeverityLevel, StagingResult
from oswaldo.engine.staging.base import StagingStrategy


class ADAStagingStrategy(StagingStrategy):
    """Estrategia de estadiamento ADA para DM2 baseado em HbA1c."""

    def calculate_stage(self, observations: dict[str, Any]) -> StagingResult:
        hba1c = observations.get("hba1c")
        stage, label, severity = self._calculate_hba1c_stage(hba1c)
        axes = {"hba1c_control": stage} if stage != "UNKNOWN" else {}

        return StagingResult(
            disease_id=self.profile.id,
            stage=stage,
            stage_label=label,
            severity=severity,
            axes=axes,
            timestamp=datetime.now(),
            observations_used=observations,
        )

    def _calculate_hba1c_stage(self, hba1c: float | None) -> tuple[str, str, SeverityLevel]:
        if hba1c is None:
            return ("UNKNOWN", "Unknown", SeverityLevel.INFO)
        if hba1c < 7.0:
            return ("CONTROLLED", "Controlado", SeverityLevel.INFO)
        if hba1c < 8.0:
            return ("SUBOPTIMAL", "Controle Subotimo", SeverityLevel.WARNING)
        if hba1c < 9.0:
            return ("POOR", "Controle Inadequado", SeverityLevel.WARNING)
        return ("VERY_POOR", "Descontrolado", SeverityLevel.CRITICAL)
