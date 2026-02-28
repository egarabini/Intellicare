"""Tradução de SMART scopes → ResourceRule (IntelliCare Access Policies).

SMART on FHIR define scopes no formato:
    {context}/{resource}.{permission}
    context:    patient | user | system
    resource:   Patient | Observation | * (wildcard)
    permission: read | write | * (both)

Esta camada traduz esses scopes em ResourceRules compatíveis com o
PolicyEvaluator do intellicare_core.access.
"""

from __future__ import annotations

import re
from typing import Optional

# SMART scope regex: context/Resource.permission
_SCOPE_RE = re.compile(
    r"^(patient|user|system)/(\*|[A-Z][a-zA-Z]+)\.(read|write|\*)$"
)

# Interactions FHIR por permissão SMART
_READ_INTERACTIONS  = ["search", "read", "vread", "history"]
_WRITE_INTERACTIONS = ["create", "update", "delete"]
_ALL_INTERACTIONS   = _READ_INTERACTIONS + _WRITE_INTERACTIONS


def parse_smart_scopes(scope_string: str) -> list[tuple[str, str, str]]:
    """Parse SMART scope string into list of (context, resource_type, permission).

    Ignores non-SMART tokens (e.g. 'openid', 'fhirUser').

    Examples:
        "patient/Patient.read" → [("patient", "Patient", "read")]
        "user/*.write"          → [("user", "*", "write")]
        "openid profile"        → []
    """
    result: list[tuple[str, str, str]] = []
    for token in scope_string.split():
        m = _SCOPE_RE.match(token)
        if m:
            result.append((m.group(1), m.group(2), m.group(3)))
    return result


def smart_scopes_to_rules(
    scope_string: str,
    *,
    allowed_resource_types: Optional[list[str]] = None,
) -> list[dict]:
    """Convert SMART scope string to IntelliCare ResourceRule dicts.

    Args:
        scope_string: Space-separated SMART scope string from token.
        allowed_resource_types: If provided, restrict to these resource types only.
            Useful to generate rules constrained to a patient's data.

    Returns:
        List of ResourceRule-compatible dicts (matching intellicare_core.access models).

    Examples:
        "patient/Patient.read" → [{"resource_type": "Patient", "interaction": ["search", "read", ...]}]
        "patient/*.read"       → one rule per resource type (or wildcard if no allowed_resource_types)
    """
    parsed = parse_smart_scopes(scope_string)
    if not parsed:
        return []

    # Build a map: resource_type → set of interactions
    rule_map: dict[str, set[str]] = {}

    for context, resource_type, permission in parsed:
        interactions: set[str] = set()
        if permission == "read":
            interactions = set(_READ_INTERACTIONS)
        elif permission == "write":
            interactions = set(_WRITE_INTERACTIONS)
        else:  # "*"
            interactions = set(_ALL_INTERACTIONS)

        if resource_type == "*":
            # Wildcard: either expand to allowed_resource_types or use sentinel "*"
            targets = allowed_resource_types if allowed_resource_types else ["*"]
            for rt in targets:
                rule_map.setdefault(rt, set()).update(interactions)
        else:
            if allowed_resource_types and resource_type not in allowed_resource_types:
                continue  # Not in allowed list — skip
            rule_map.setdefault(resource_type, set()).update(interactions)

    rules = []
    for rt, interactions in rule_map.items():
        # Order interactions for determinism
        ordered = [i for i in _ALL_INTERACTIONS if i in interactions]
        rules.append({"resource_type": rt, "interaction": ordered})

    return sorted(rules, key=lambda r: r["resource_type"])
