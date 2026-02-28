"""FHIR SearchParameter registry — maps search param codes to JSON paths + types.

Covers the most commonly used FHIR R4 search parameters for IntelliCare's
primary resource types.

SearchParamDef fields:
    type:   string | token | date | reference | number | quantity | uri
    paths:  List of JSON dot-paths (supports [*] for arrays)
    base:   Resource type(s) this parameter applies to
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


SearchParamType = Literal[
    "string", "token", "date", "reference", "number", "quantity", "uri", "special"
]


@dataclass
class SearchParamDef:
    code: str
    type: SearchParamType
    paths: list[str]
    """JSON dot-paths. Use [*] for array traversal."""
    description: str = ""
    base: list[str] = field(default_factory=list)


# ── Common search parameters (shared across resource types) ──────────────────

_COMMON = {
    "_id": SearchParamDef(
        code="_id",
        type="token",
        paths=["id"],
        description="Resource FHIR id",
    ),
    "_lastUpdated": SearchParamDef(
        code="_lastUpdated",
        type="date",
        paths=["meta.lastUpdated"],
        description="Last update timestamp",
    ),
    "_tag": SearchParamDef(
        code="_tag",
        type="token",
        paths=["meta.tag[*].code"],
    ),
    "_profile": SearchParamDef(
        code="_profile",
        type="uri",
        paths=["meta.profile[*]"],
    ),
}

# ── Per-ResourceType search parameters ───────────────────────────────────────

SEARCH_PARAMS: dict[str, dict[str, SearchParamDef]] = {
    # ── Patient ───────────────────────────────────────────────────────────
    "Patient": {
        **_COMMON,
        "name": SearchParamDef(
            code="name",
            type="string",
            paths=["name[*].family", "name[*].given[*]", "name[*].text"],
            base=["Patient"],
        ),
        "family": SearchParamDef(
            code="family",
            type="string",
            paths=["name[*].family"],
            base=["Patient"],
        ),
        "given": SearchParamDef(
            code="given",
            type="string",
            paths=["name[*].given[*]"],
            base=["Patient"],
        ),
        "birthdate": SearchParamDef(
            code="birthdate",
            type="date",
            paths=["birthDate"],
            base=["Patient"],
        ),
        "gender": SearchParamDef(
            code="gender",
            type="token",
            paths=["gender"],
            base=["Patient"],
        ),
        "active": SearchParamDef(
            code="active",
            type="token",
            paths=["active"],
            base=["Patient"],
        ),
        "identifier": SearchParamDef(
            code="identifier",
            type="token",
            paths=["identifier[*].value", "identifier[*].system"],
            base=["Patient"],
        ),
        "general-practitioner": SearchParamDef(
            code="general-practitioner",
            type="reference",
            paths=["generalPractitioner[*].reference"],
            base=["Patient"],
        ),
    },

    # ── Observation ───────────────────────────────────────────────────────
    "Observation": {
        **_COMMON,
        "status": SearchParamDef(
            code="status",
            type="token",
            paths=["status"],
            base=["Observation"],
        ),
        "code": SearchParamDef(
            code="code",
            type="token",
            paths=["code.coding[*].code", "code.text"],
            base=["Observation"],
        ),
        "subject": SearchParamDef(
            code="subject",
            type="reference",
            paths=["subject.reference"],
            base=["Observation"],
        ),
        "patient": SearchParamDef(
            code="patient",
            type="reference",
            paths=["subject.reference"],
            base=["Observation"],
        ),
        "date": SearchParamDef(
            code="date",
            type="date",
            paths=["effectiveDateTime", "effectivePeriod.start"],
            base=["Observation"],
        ),
        "value-quantity": SearchParamDef(
            code="value-quantity",
            type="quantity",
            paths=["valueQuantity.value"],
            base=["Observation"],
        ),
        "performer": SearchParamDef(
            code="performer",
            type="reference",
            paths=["performer[*].reference"],
            base=["Observation"],
        ),
        "category": SearchParamDef(
            code="category",
            type="token",
            paths=["category[*].coding[*].code"],
            base=["Observation"],
        ),
    },

    # ── Encounter ─────────────────────────────────────────────────────────
    "Encounter": {
        **_COMMON,
        "status": SearchParamDef(
            code="status",
            type="token",
            paths=["status"],
            base=["Encounter"],
        ),
        "subject": SearchParamDef(
            code="subject",
            type="reference",
            paths=["subject.reference"],
            base=["Encounter"],
        ),
        "patient": SearchParamDef(
            code="patient",
            type="reference",
            paths=["subject.reference"],
            base=["Encounter"],
        ),
        "date": SearchParamDef(
            code="date",
            type="date",
            paths=["period.start"],
            base=["Encounter"],
        ),
        "class": SearchParamDef(
            code="class",
            type="token",
            paths=["class.code"],
            base=["Encounter"],
        ),
        "service-provider": SearchParamDef(
            code="service-provider",
            type="reference",
            paths=["serviceProvider.reference"],
            base=["Encounter"],
        ),
    },

    # ── MedicationRequest ─────────────────────────────────────────────────
    "MedicationRequest": {
        **_COMMON,
        "status": SearchParamDef(
            code="status",
            type="token",
            paths=["status"],
            base=["MedicationRequest"],
        ),
        "subject": SearchParamDef(
            code="subject",
            type="reference",
            paths=["subject.reference"],
            base=["MedicationRequest"],
        ),
        "patient": SearchParamDef(
            code="patient",
            type="reference",
            paths=["subject.reference"],
            base=["MedicationRequest"],
        ),
        "intent": SearchParamDef(
            code="intent",
            type="token",
            paths=["intent"],
            base=["MedicationRequest"],
        ),
        "medication": SearchParamDef(
            code="medication",
            type="reference",
            paths=["medicationReference.reference", "medicationCodeableConcept.coding[*].code"],
            base=["MedicationRequest"],
        ),
        "requester": SearchParamDef(
            code="requester",
            type="reference",
            paths=["requester.reference"],
            base=["MedicationRequest"],
        ),
    },

    # ── Practitioner ──────────────────────────────────────────────────────
    "Practitioner": {
        **_COMMON,
        "name": SearchParamDef(
            code="name",
            type="string",
            paths=["name[*].family", "name[*].given[*]", "name[*].text"],
            base=["Practitioner"],
        ),
        "identifier": SearchParamDef(
            code="identifier",
            type="token",
            paths=["identifier[*].value"],
            base=["Practitioner"],
        ),
        "active": SearchParamDef(
            code="active",
            type="token",
            paths=["active"],
            base=["Practitioner"],
        ),
    },

    # ── Organization ──────────────────────────────────────────────────────
    "Organization": {
        **_COMMON,
        "name": SearchParamDef(
            code="name",
            type="string",
            paths=["name"],
            base=["Organization"],
        ),
        "active": SearchParamDef(
            code="active",
            type="token",
            paths=["active"],
            base=["Organization"],
        ),
        "type": SearchParamDef(
            code="type",
            type="token",
            paths=["type[*].coding[*].code"],
            base=["Organization"],
        ),
    },

    # ── Condition ─────────────────────────────────────────────────────────
    "Condition": {
        **_COMMON,
        "status": SearchParamDef(
            code="status",
            type="token",
            paths=["clinicalStatus.coding[*].code"],
            base=["Condition"],
        ),
        "subject": SearchParamDef(
            code="subject",
            type="reference",
            paths=["subject.reference"],
            base=["Condition"],
        ),
        "patient": SearchParamDef(
            code="patient",
            type="reference",
            paths=["subject.reference"],
            base=["Condition"],
        ),
        "code": SearchParamDef(
            code="code",
            type="token",
            paths=["code.coding[*].code"],
            base=["Condition"],
        ),
        "category": SearchParamDef(
            code="category",
            type="token",
            paths=["category[*].coding[*].code"],
            base=["Condition"],
        ),
    },

    # ── DiagnosticReport ──────────────────────────────────────────────────
    "DiagnosticReport": {
        **_COMMON,
        "status": SearchParamDef(
            code="status",
            type="token",
            paths=["status"],
        ),
        "subject": SearchParamDef(
            code="subject",
            type="reference",
            paths=["subject.reference"],
        ),
        "patient": SearchParamDef(
            code="patient",
            type="reference",
            paths=["subject.reference"],
        ),
        "code": SearchParamDef(
            code="code",
            type="token",
            paths=["code.coding[*].code"],
        ),
        "date": SearchParamDef(
            code="date",
            type="date",
            paths=["effectiveDateTime", "effectivePeriod.start"],
        ),
    },
}

# Fallback for resource types not in the registry (use only common params)
_FALLBACK: dict[str, SearchParamDef] = dict(_COMMON)


def get_search_param(
    resource_type: str, code: str
) -> SearchParamDef | None:
    """Look up a SearchParamDef by resource type and code.

    Falls back to common params if resource type not in registry.
    Returns None if code is unknown.
    """
    params = SEARCH_PARAMS.get(resource_type, _FALLBACK)
    return params.get(code) or _COMMON.get(code)
