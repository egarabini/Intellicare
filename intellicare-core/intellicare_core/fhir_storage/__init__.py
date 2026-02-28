"""FHIR-Native Storage — versioned FHIR resource persistence.

Provides:
    - FHIRNativeResource ORM model (fhir_native_resources table)
    - FHIRResourceHistory ORM model (fhir_native_history table)
    - FHIRRepository — CRUD + versioning + history + vread
    - Compartment helpers
"""

from .compartments import extract_compartments
from .models import FHIRNativeResource, FHIRResourceHistory
from .repository import FHIRRepository

__all__ = [
    "FHIRNativeResource",
    "FHIRResourceHistory",
    "FHIRRepository",
    "extract_compartments",
]
