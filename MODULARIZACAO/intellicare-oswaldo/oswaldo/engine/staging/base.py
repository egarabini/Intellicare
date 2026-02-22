"""Staging Strategy — interface abstrata para estrategias de estadiamento."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from oswaldo.engine.models import SeverityLevel, StagingResult
from oswaldo.profiles.models import DiseaseProfile, StagingAxisConfig


class StagingStrategy(ABC):
    """Interface abstrata para estrategias de estadiamento."""

    def __init__(self, profile: DiseaseProfile) -> None:
        self.profile = profile
        self.staging_config = profile.staging

    @abstractmethod
    def calculate_stage(self, observations: dict[str, Any]) -> StagingResult:
        """Calcula estagio da doenca baseado em observacoes."""

    def _get_observation_value(self, observations: dict[str, Any], observation_id: str) -> Any | None:
        return observations.get(observation_id)

    def _calculate_axis_stage(self, axis: StagingAxisConfig, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        for stage_config in axis.stages:
            min_val = stage_config.get("min")
            max_val = stage_config.get("max")
            if self._value_in_range(value, min_val, max_val):
                return {
                    "axis_id": axis.id,
                    "stage": stage_config["stage"],
                    "label": stage_config["label"],
                    "severity": stage_config["severity"],
                    "value": value,
                }
        return None

    def _value_in_range(self, value: float, min_val: float | None, max_val: float | None) -> bool:
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value >= max_val:
            return False
        return True

    def _combine_severities(self, severities: list[str]) -> SeverityLevel:
        if not severities:
            return SeverityLevel.INFO
        if "critical" in severities:
            return SeverityLevel.CRITICAL
        if "warning" in severities:
            return SeverityLevel.WARNING
        return SeverityLevel.INFO


class GenericRangeStagingStrategy(StagingStrategy):
    """Estrategia generica baseada em ranges numericos."""

    def calculate_stage(self, observations: dict[str, Any]) -> StagingResult:
        axes_results = []
        severities = []
        for axis in self.staging_config.axes:
            value = self._get_observation_value(observations, axis.observation_id)
            if value is not None:
                axis_result = self._calculate_axis_stage(axis, value)
                if axis_result:
                    axes_results.append(axis_result)
                    severities.append(axis_result["severity"])

        if not axes_results:
            return StagingResult(
                disease_id=self.profile.id,
                stage="UNKNOWN",
                stage_label="Unknown",
                severity=SeverityLevel.INFO,
                axes={},
                timestamp=datetime.now(),
                observations_used=observations,
            )

        overall_severity = self._combine_severities(severities)
        if len(axes_results) == 1:
            main_stage = axes_results[0]["stage"]
            main_label = axes_results[0]["label"]
        else:
            main_stage = "_".join([r["stage"] for r in axes_results])
            main_label = " + ".join([r["label"] for r in axes_results])
        axes_dict = {r["axis_id"]: r["stage"] for r in axes_results}

        return StagingResult(
            disease_id=self.profile.id,
            stage=main_stage,
            stage_label=main_label,
            severity=overall_severity,
            axes=axes_dict,
            timestamp=datetime.now(),
            observations_used=observations,
        )
