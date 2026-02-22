"""Cliente FHIR R4 para modulos IntelliCare."""

from intellicare_core.fhir.client import FHIRClient
from intellicare_core.fhir.models import (
    PatientSummary,
    ConditionSummary,
    ObservationValue,
)

__all__ = [
    "FHIRClient",
    "PatientSummary",
    "ConditionSummary",
    "ObservationValue",
]
