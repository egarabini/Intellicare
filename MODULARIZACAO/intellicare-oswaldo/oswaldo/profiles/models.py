"""Modelos de perfis de doencas."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ObservationConfig:
    """Configuracao de uma observacao monitorada."""

    id: str
    name: str
    name_short: str
    loinc_code: str
    unit: str
    type: str
    reference_ranges: dict[str, dict[str, float | None]]
    trend_direction: str
    target: dict[str, float] | None = None
    components: list["ObservationConfig"] = field(default_factory=list)
    category: str = "lab"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObservationConfig":
        components = [cls.from_dict(c) for c in data.get("components", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            name_short=data["name_short"],
            loinc_code=data["loinc_code"],
            unit=data["unit"],
            type=data["type"],
            reference_ranges=data["reference_ranges"],
            trend_direction=data["trend_direction"],
            target=data.get("target"),
            components=components,
            category=data.get("category", "lab"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "name_short": self.name_short,
            "loinc_code": self.loinc_code,
            "unit": self.unit,
            "type": self.type,
            "reference_ranges": self.reference_ranges,
            "trend_direction": self.trend_direction,
            "category": self.category,
        }
        if self.target:
            result["target"] = self.target
        if self.components:
            result["components"] = [c.to_dict() for c in self.components]
        return result


@dataclass
class StagingAxisConfig:
    """Configuracao de um eixo de estadiamento."""

    id: str
    name: str
    observation_id: str
    stages: list[dict[str, Any]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StagingAxisConfig":
        return cls(id=data["id"], name=data["name"], observation_id=data["observation_id"], stages=data["stages"])

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "observation_id": self.observation_id, "stages": self.stages}


@dataclass
class StagingConfig:
    """Configuracao de estadiamento."""

    strategy: str
    axes: list[StagingAxisConfig]
    combine_method: str = "worst"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StagingConfig":
        axes = [StagingAxisConfig.from_dict(a) for a in data.get("axes", [])]
        return cls(strategy=data["strategy"], axes=axes, combine_method=data.get("combine_method", "worst"))

    def to_dict(self) -> dict[str, Any]:
        return {"strategy": self.strategy, "axes": [a.to_dict() for a in self.axes], "combine_method": self.combine_method}


@dataclass
class AlertConfig:
    """Configuracao de alerta."""

    id: str
    type: str
    observation_id: str
    condition: str
    threshold: Any
    severity: str
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlertConfig":
        return cls(
            id=data["id"],
            type=data["type"],
            observation_id=data["observation_id"],
            condition=data["condition"],
            threshold=data["threshold"],
            severity=data["severity"],
            message=data["message"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "observation_id": self.observation_id,
            "condition": self.condition,
            "threshold": self.threshold,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass
class DiseaseProfile:
    """Perfil completo de uma doenca cronica."""

    id: str
    name: str
    description: str
    version: str
    snomed_code: str
    observations: list[ObservationConfig]
    staging: StagingConfig
    alerts: list[AlertConfig]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiseaseProfile":
        observations = [ObservationConfig.from_dict(o) for o in data.get("observations", [])]
        staging = StagingConfig.from_dict(data["staging"])
        alerts = [AlertConfig.from_dict(a) for a in data.get("alerts", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            version=data["version"],
            snomed_code=data["snomed_code"],
            observations=observations,
            staging=staging,
            alerts=alerts,
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "snomed_code": self.snomed_code,
            "observations": [o.to_dict() for o in self.observations],
            "staging": self.staging.to_dict(),
            "alerts": [a.to_dict() for a in self.alerts],
            "metadata": self.metadata,
        }

    def get_observation(self, observation_id: str) -> ObservationConfig | None:
        for obs in self.observations:
            if obs.id == observation_id:
                return obs
        return None
