"""Pydantic models for FHIR R4 Terminology Service operations."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CodeSystemConcept(BaseModel):
    """A single concept in a code system."""

    system: str
    code: str
    display: str
    definition: Optional[str] = None
    # Additional designations (e.g. pt-BR translation)
    designations: dict[str, str] = {}
    # Parent code for hierarchical systems (e.g. ICD-10 chapters)
    parent: Optional[str] = None
    # Arbitrary properties (e.g. LOINC component, scale)
    properties: dict[str, str] = {}


class ValueSetExpansion(BaseModel):
    """Result of a ValueSet/$expand operation."""

    url: str
    total: int
    concepts: list[CodeSystemConcept]


class TranslationMatch(BaseModel):
    """A single match from a ConceptMap/$translate operation."""

    equivalence: str  # "equivalent" | "wider" | "narrower" | "unmatched"
    concept: Optional[CodeSystemConcept] = None
