"""Compartment helpers — extract compartment references from FHIR resources.

A compartment reference is a FHIR reference string like 'Patient/123'
or 'Organization/setor-a'.  Resources are indexed by their compartments so
they can be efficiently filtered in queries like:

    GET /fhir/Patient/123/Observation
    (= all Observations in Patient/123 compartment)
"""

from __future__ import annotations

from typing import Any


def extract_compartments(resource: dict[str, Any]) -> list[str]:
    """Return a list of compartment references for *resource*.

    Covers the most common FHIR compartments:
        - Patient     (patient-centric resources)
        - Organization (organization-scoped resources)
        - Practitioner (practitioner-authored resources)
        - Encounter    (encounter-linked resources)

    Returns de-duplicated list of strings like ['Patient/p-001', 'Organization/org-a'].
    """
    compartments: set[str] = set()
    resource_type = resource.get("resourceType", "")
    fhir_id = resource.get("id", "")

    # ── The resource IS a compartment owner ───────────────────────────────
    if resource_type in ("Patient", "Organization", "Practitioner", "Encounter"):
        if fhir_id:
            compartments.add(f"{resource_type}/{fhir_id}")

    # ── Patient compartment ───────────────────────────────────────────────
    _add_ref(compartments, resource, "subject.reference", "Patient")
    _add_ref(compartments, resource, "patient.reference", "Patient")

    # Multiple subjects / patients
    for entry in resource.get("subject", []) if isinstance(resource.get("subject"), list) else []:
        r = entry.get("reference", "")
        if r.startswith("Patient/"):
            compartments.add(r)

    # ── Organization compartment ──────────────────────────────────────────
    _add_ref(compartments, resource, "managingOrganization.reference", "Organization")
    _add_ref(compartments, resource, "serviceProvider.reference", "Organization")

    # ── Practitioner compartment ──────────────────────────────────────────
    _add_ref(compartments, resource, "author.reference", "Practitioner")
    _add_ref(compartments, resource, "requester.reference", "Practitioner")
    # performers (list)
    for entry in resource.get("performer", []):
        if isinstance(entry, dict):
            r = entry.get("reference", "")
            if r.startswith("Practitioner/"):
                compartments.add(r)

    # ── Encounter compartment ─────────────────────────────────────────────
    _add_ref(compartments, resource, "encounter.reference", "Encounter")
    _add_ref(compartments, resource, "context.reference", "Encounter")

    return sorted(compartments)


def _add_ref(
    compartments: set[str], resource: dict[str, Any], dot_path: str, expected_type: str
) -> None:
    """Traverse *dot_path* in *resource* and add the reference if it starts with *expected_type*."""
    parts = dot_path.split(".")
    obj: Any = resource
    for part in parts:
        if not isinstance(obj, dict):
            return
        obj = obj.get(part)
    if isinstance(obj, str) and obj.startswith(f"{expected_type}/"):
        compartments.add(obj)
