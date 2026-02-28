"""FHIR R4 Terminology Service — $lookup, $expand, $validate-code, $translate.

Public API:
    Models:   CodeSystemConcept, ValueSetExpansion, TranslationMatch
    Registry: TerminologyRegistry (singleton via get_registry())
    Ops:      lookup(), expand(), validate_code(), translate()
"""

from .models import CodeSystemConcept, TranslationMatch, ValueSetExpansion
from .registry import TerminologyRegistry, get_registry
from .operations import expand, lookup, translate, validate_code

__all__ = [
    "CodeSystemConcept",
    "TranslationMatch",
    "ValueSetExpansion",
    "TerminologyRegistry",
    "get_registry",
    "expand",
    "lookup",
    "translate",
    "validate_code",
]
