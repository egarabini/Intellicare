"""Data models for the IPS subsystem (EF-W002)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class IPSBundle:
    """International Patient Summary — FHIR Bundle representation.

    Contains:
    - Patient demographics
    - Conditions (active diagnoses)
    - MedicationStatements
    - AllergyIntolerances
    - Observations (lab results, vital signs)
    - Immunizations
    """

    patient_id: str
    patient_name: str = ""

    # Clinical data
    conditions: list[dict[str, Any]] = field(default_factory=list)
    medications: list[dict[str, Any]] = field(default_factory=list)
    allergies: list[dict[str, Any]] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    immunizations: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    source: str = "unknown"  # florence, cache, stale, degraded, empty
    fetched_at: Optional[datetime] = None
    age_seconds: float = 0.0
    is_stale: bool = False
    is_degraded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "conditions": self.conditions,
            "medications": self.medications,
            "allergies": self.allergies,
            "observations": self.observations,
            "immunizations": self.immunizations,
            "source": self.source,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "age_seconds": round(self.age_seconds, 1),
            "is_stale": self.is_stale,
            "is_degraded": self.is_degraded,
        }

    @classmethod
    def from_florence_response(cls, patient_id: str, data: dict) -> "IPSBundle":
        """Parse IPS from Florence's /api/v1/ips/{patient_id} response."""
        return cls(
            patient_id=patient_id,
            patient_name=data.get("patient_name", ""),
            conditions=data.get("conditions", []),
            medications=data.get("medications", []),
            allergies=data.get("allergies", []),
            observations=data.get("observations", []),
            immunizations=data.get("immunizations", []),
            source="florence",
            fetched_at=datetime.now(),
        )

    @classmethod
    def empty(cls, patient_id: str) -> "IPSBundle":
        """Create an empty IPS (last resort fallback)."""
        return cls(
            patient_id=patient_id,
            source="empty",
            is_degraded=True,
            fetched_at=datetime.now(),
        )


@dataclass
class EnrichedIPS:
    """IPS enriched with data from specialized agents."""

    ips: IPSBundle

    # Oswaldo enrichment (chronic disease staging)
    staging: dict[str, Any] = field(default_factory=dict)

    # Geralda enrichment (care journey)
    care: dict[str, Any] = field(default_factory=dict)

    # Enrichment metadata
    enriched_sources: list[str] = field(default_factory=list)
    enriched_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        result = self.ips.to_dict()
        result["staging"] = self.staging
        result["care"] = self.care
        result["enriched_sources"] = self.enriched_sources
        result["enriched_at"] = (
            self.enriched_at.isoformat() if self.enriched_at else None
        )
        return result


@dataclass
class ValidationResult:
    """Result of IPS validation."""

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }
