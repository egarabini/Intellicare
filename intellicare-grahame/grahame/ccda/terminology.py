"""Terminology and status normalization helpers for CCDA -> FHIR."""

from __future__ import annotations

from typing import Any

OID_TO_FHIR_SYSTEM: dict[str, str] = {
    "2.16.840.1.113883.6.1": "http://loinc.org",
    "2.16.840.1.113883.6.90": "http://hl7.org/fhir/sid/icd-10",
    "2.16.840.1.113883.6.96": "http://snomed.info/sct",
    "2.16.840.1.113883.6.88": "http://www.nlm.nih.gov/research/umls/rxnorm",
    "2.16.840.1.113883.12.292": "http://hl7.org/fhir/sid/cvx",
    "2.16.840.1.113883.5.4": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "2.16.840.1.113883.5.112": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
}


def normalize_system(system: str | None) -> str | None:
    if not system:
        return system
    normalized = system.strip()
    if normalized.startswith("urn:oid:"):
        oid = normalized.removeprefix("urn:oid:")
        return OID_TO_FHIR_SYSTEM.get(oid, normalized)
    if normalized.startswith("2.") and all(part.isdigit() for part in normalized.split(".")):
        return OID_TO_FHIR_SYSTEM.get(normalized, f"urn:oid:{normalized}")
    return normalized


def normalize_coding(coding: dict[str, Any] | None) -> dict[str, Any]:
    if not coding:
        return {}
    result = dict(coding)
    result["system"] = normalize_system(result.get("system"))
    return {k: v for k, v in result.items() if v is not None and v != ""}


def map_condition_status(raw_status: str | None) -> str:
    val = _norm(raw_status)
    mapping = {
        "active": "active",
        "completed": "resolved",
        "resolved": "resolved",
        "inactive": "inactive",
        "suspended": "inactive",
        "aborted": "inactive",
        "cancelled": "inactive",
    }
    return mapping.get(val, "active")


def map_medication_request_status(raw_status: str | None) -> str:
    val = _norm(raw_status)
    mapping = {
        "active": "active",
        "completed": "completed",
        "suspended": "on-hold",
        "hold": "on-hold",
        "aborted": "stopped",
        "stopped": "stopped",
        "cancelled": "cancelled",
        "nullified": "entered-in-error",
        "new": "draft",
    }
    return mapping.get(val, "unknown")


def map_observation_status(raw_status: str | None) -> str:
    val = _norm(raw_status)
    mapping = {
        "active": "preliminary",
        "new": "registered",
        "preliminary": "preliminary",
        "final": "final",
        "completed": "final",
        "amended": "amended",
        "corrected": "corrected",
        "cancelled": "cancelled",
        "aborted": "cancelled",
        "nullified": "entered-in-error",
    }
    return mapping.get(val, "unknown")


def map_procedure_status(raw_status: str | None) -> str:
    val = _norm(raw_status)
    mapping = {
        "new": "preparation",
        "active": "in-progress",
        "suspended": "on-hold",
        "aborted": "stopped",
        "completed": "completed",
        "cancelled": "not-done",
        "nullified": "entered-in-error",
    }
    return mapping.get(val, "unknown")


def map_immunization_status(raw_status: str | None) -> str:
    val = _norm(raw_status)
    mapping = {
        "completed": "completed",
        "active": "completed",
        "cancelled": "not-done",
        "aborted": "not-done",
        "nullified": "entered-in-error",
    }
    return mapping.get(val, "completed")


def map_encounter_status(raw_status: str | None) -> str:
    val = _norm(raw_status)
    mapping = {
        "new": "planned",
        "active": "in-progress",
        "arrived": "arrived",
        "triaged": "triaged",
        "onleave": "onleave",
        "completed": "finished",
        "finished": "finished",
        "cancelled": "cancelled",
        "aborted": "cancelled",
    }
    return mapping.get(val, "unknown")


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()
