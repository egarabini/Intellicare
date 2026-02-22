"""KDIGO Staging Strategy — Doenca Renal Cronica (KDIGO 2012)."""

from datetime import datetime
from typing import Any

from oswaldo.engine.models import SeverityLevel, StagingResult
from oswaldo.engine.staging.base import StagingStrategy


class KDIGOStagingStrategy(StagingStrategy):
    """Estrategia de estadiamento KDIGO para DRC.

    Eixos: G (eGFR: G1-G5), A (ACR: A1-A3).
    """

    def calculate_stage(self, observations: dict[str, Any]) -> StagingResult:
        egfr = observations.get("egfr")
        acr = observations.get("acr")

        g_stage, g_label, g_severity = self._calculate_g_stage(egfr)
        a_stage, a_label, a_severity = self._calculate_a_stage(acr)

        if g_stage != "NA" and a_stage != "NA":
            combined_stage = f"{g_stage}_{a_stage}"
            combined_label = f"{g_label} + {a_label}"
            axes = {"gfr": g_stage, "acr": a_stage}
        elif g_stage != "NA":
            combined_stage = g_stage
            combined_label = g_label
            axes = {"gfr": g_stage}
        elif a_stage != "NA":
            combined_stage = a_stage
            combined_label = a_label
            axes = {"acr": a_stage}
        else:
            combined_stage = "UNKNOWN"
            combined_label = "Unknown"
            axes = {}

        overall_severity = self._combine_severities([g_severity, a_severity])

        return StagingResult(
            disease_id=self.profile.id,
            stage=combined_stage,
            stage_label=combined_label,
            severity=overall_severity,
            axes=axes,
            timestamp=datetime.now(),
            observations_used=observations,
        )

    def _calculate_g_stage(self, egfr: float | None) -> tuple[str, str, str]:
        if egfr is None:
            return ("NA", "Not Available", "info")
        if egfr >= 90:
            return ("G1", "Normal ou elevada", "info")
        if egfr >= 60:
            return ("G2", "Levemente diminuida", "info")
        if egfr >= 45:
            return ("G3a", "Leve a moderadamente diminuida", "warning")
        if egfr >= 30:
            return ("G3b", "Moderada a severamente diminuida", "warning")
        if egfr >= 15:
            return ("G4", "Severamente diminuida", "critical")
        return ("G5", "Falencia renal", "critical")

    def _calculate_a_stage(self, acr: float | None) -> tuple[str, str, str]:
        if acr is None:
            return ("NA", "Not Available", "info")
        if acr < 30:
            return ("A1", "Normal a levemente aumentada", "info")
        if acr <= 300:
            return ("A2", "Moderadamente aumentada", "warning")
        return ("A3", "Severamente aumentada", "critical")
