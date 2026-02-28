"""SMART-on-FHIR scope → AccessPolicy translation.

Supports SMART App Launch scope syntax:
  - patient/*.read
  - user/Observation.write
  - system/Patient.read
  - patient/Patient.*

This is a preview implementation; full SMART Launch is deferred to Onda 4.
"""

from __future__ import annotations

import re
from typing import Optional

from .models import EffectiveAccessPolicy, ResourceRule

# Matches: (context)/(ResourceType|*).(permission|*)
# context: patient | user | system
# permission: read | write | * (read+write)
_SCOPE_RE = re.compile(
    r"^(patient|user|system)/(\*|[A-Z][a-zA-Z]+)\.(read|write|\*)$"
)

_READ_INTERACTIONS = ["search", "read"]
_WRITE_INTERACTIONS = ["create", "update", "delete"]
_ALL_INTERACTIONS = _READ_INTERACTIONS + _WRITE_INTERACTIONS


def parse_smart_scopes(scope_string: str) -> list[tuple[str, str, str]]:
    """Parse a space-separated SMART scope string.

    Returns a list of (context, resource_type, permission) tuples.
    Unknown / malformed scopes are silently ignored.
    """
    parsed = []
    for token in scope_string.split():
        m = _SCOPE_RE.match(token)
        if m:
            parsed.append((m.group(1), m.group(2), m.group(3)))
    return parsed


def _permission_to_interactions(permission: str) -> list[str]:
    if permission == "read":
        return list(_READ_INTERACTIONS)
    if permission == "write":
        return list(_WRITE_INTERACTIONS)
    # "*" → all
    return list(_ALL_INTERACTIONS)


def _smart_rules_from_scopes(
    scopes: list[tuple[str, str, str]]
) -> list[ResourceRule]:
    """Build ResourceRule list from parsed SMART scopes."""
    # Accumulate per resource_type
    by_type: dict[str, set[str]] = {}
    for _ctx, resource_type, permission in scopes:
        interactions = _permission_to_interactions(permission)
        key = resource_type if resource_type != "*" else "*"
        by_type.setdefault(key, set()).update(interactions)

    rules = []
    for resource_type, interactions in by_type.items():
        allowed = [i for i in _ALL_INTERACTIONS if i in interactions]
        rules.append(ResourceRule(resource_type=resource_type, interaction=allowed))

    return rules


def apply_smart_scopes(
    policy: EffectiveAccessPolicy,
    scope_string: Optional[str],
) -> EffectiveAccessPolicy:
    """Restrict *policy* by the SMART scopes in *scope_string*.

    The result is the *intersection* of the original policy rules and the
    SMART scope permissions — i.e., scopes can only restrict, never expand.

    If *scope_string* is empty or None the policy is returned unchanged.
    """
    if not scope_string:
        return policy

    scopes = parse_smart_scopes(scope_string)
    if not scopes:
        return policy

    smart_rules = _smart_rules_from_scopes(scopes)
    smart_by_type = {r.resource_type: r for r in smart_rules}

    narrowed: list[ResourceRule] = []

    for rule in policy.rules:
        # Find the matching SMART rule (exact or wildcard "*")
        smart_rule = smart_by_type.get(rule.resource_type) or smart_by_type.get("*")

        if smart_rule is None:
            # No SMART scope grants access to this resource type → exclude
            continue

        # Intersect interactions
        policy_interactions = set(rule.interaction or _ALL_INTERACTIONS)
        smart_interactions = set(smart_rule.interaction or _ALL_INTERACTIONS)
        allowed = list(policy_interactions & smart_interactions)

        if not allowed:
            continue

        narrowed.append(
            ResourceRule(
                resource_type=rule.resource_type,
                interaction=allowed,
                criteria=rule.criteria,
                readonly=rule.readonly,
                readonly_fields=rule.readonly_fields,
                hidden_fields=rule.hidden_fields,
            )
        )

    return EffectiveAccessPolicy(
        rules=narrowed,
        is_admin=policy.is_admin,
        compartment_ref=policy.compartment_ref,
        user_id=policy.user_id,
        tenant_id=policy.tenant_id,
    )
