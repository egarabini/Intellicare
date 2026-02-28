"""Linguagem acessível para comunicação com pacientes."""

from geralda.ai.language.medical_glossary import (
    MEDICAL_GLOSSARY,
    simplify_term,
    has_translation,
    get_all_terms,
)
from geralda.ai.language.simplifier import MedicalSimplifier
from geralda.ai.language.formatter import OutputFormatter

__all__ = [
    "MEDICAL_GLOSSARY",
    "simplify_term",
    "has_translation",
    "get_all_terms",
    "MedicalSimplifier",
    "OutputFormatter",
]
