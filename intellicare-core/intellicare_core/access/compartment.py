"""Compartment-based scoping — restrict access to resources within an organizational unit.

A compartment reference is a FHIR reference like 'Organization/setor-a'.
Resources that have a reference to the compartment entity are accessible;
others are filtered out.

This is a preview implementation with basic compartment matching.
"""

from __future__ import annotations

import re
from typing import Any, Optional


# Known FHIR compartment definitions (resource_type → fields that may point to compartment)
_COMPARTMENT_FIELDS: dict[str, list[str]] = {
    "Patient": ["managingOrganization.reference", "generalPractitioner.*.reference"],
    "Encounter": ["serviceProvider.reference", "participant.*.individual.reference"],
    "Observation": ["subject.reference", "performer.*.reference"],
    "DiagnosticReport": ["subject.reference", "performer.*.reference"],
    "ServiceRequest": ["subject.reference", "performer.*.reference"],
    "MedicationRequest": ["subject.reference", "requester.reference"],
    "Appointment": ["participant.*.actor.reference"],
    "Practitioner": [""],
    "Organization": ["partOf.reference"],
}


class CompartmentMatcher:
    """Check whether a FHIR resource belongs to a given compartment.

    Usage::

        matcher = CompartmentMatcher("Organization/setor-a")
        if matcher.resource_in_compartment(resource):
            ...
    """

    def __init__(self, compartment_ref: str) -> None:
        self.compartment_ref = compartment_ref
        # Normalize: "Organization/setor-a"
        self._resource_type, _, self._resource_id = compartment_ref.partition("/")

    def resource_in_compartment(self, resource: dict[str, Any]) -> bool:
        """Return True if *resource* has a reference to the compartment entity."""
        resource_type = resource.get("resourceType", "")

        # If the resource IS the compartment entity itself
        if resource_type == self._resource_type and resource.get("id") == self._resource_id:
            return True

        fields = _COMPARTMENT_FIELDS.get(resource_type, [])
        for field_path in fields:
            if not field_path:
                continue
            values = _get_nested_list(resource, field_path)
            if any(self._ref_matches(v) for v in values):
                return True

        return False

    def _ref_matches(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        # Accept both "Organization/setor-a" and full URL
        return (
            value == self.compartment_ref
            or value.endswith(f"/{self._resource_type}/{self._resource_id}")
        )

    def filter_bundle(
        self, resources: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Return only resources that belong to the compartment."""
        return [r for r in resources if self.resource_in_compartment(r)]


def _get_nested_list(obj: Any, path: str) -> list[Any]:
    """Traverse a dot-path with '*' wildcard, returning a flat list of leaf values."""
    parts = path.split(".", 1)
    key = parts[0]
    rest = parts[1] if len(parts) > 1 else None

    if key == "*":
        if isinstance(obj, list):
            results = []
            for item in obj:
                results.extend(_get_nested_list(item, rest) if rest else [item])
            return results
        return []

    if isinstance(obj, dict):
        child = obj.get(key)
        if child is None:
            return []
        if rest:
            return _get_nested_list(child, rest)
        return [child] if not isinstance(child, list) else child

    if isinstance(obj, list):
        results = []
        for item in obj:
            results.extend(_get_nested_list(item, path))
        return results

    return []


def extract_compartment_from_policy(
    policy_compartment_ref: Optional[str],
) -> Optional[CompartmentMatcher]:
    """Build a CompartmentMatcher from a policy's compartment_ref, or None."""
    if not policy_compartment_ref:
        return None
    return CompartmentMatcher(policy_compartment_ref)
