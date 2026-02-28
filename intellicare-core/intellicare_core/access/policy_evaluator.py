"""PolicyEvaluator — decides whether an operation is allowed by an EffectiveAccessPolicy.

Uses FHIRCriteriaMatcher (from intellicare_core.subscriptions.matcher) for criteria checks.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .models import EffectiveAccessPolicy, ResourceRule

logger = logging.getLogger(__name__)

_WRITE_INTERACTIONS = frozenset({"create", "update", "delete"})


class PolicyEvaluator:
    """Stateless evaluator — instantiate once and reuse."""

    # ── Rule matching ──────────────────────────────────────────────────────

    def _find_rule(
        self, policy: EffectiveAccessPolicy, resource_type: str
    ) -> Optional[ResourceRule]:
        """Find the most specific matching rule (exact type > wildcard '*')."""
        exact = None
        wildcard = None
        for rule in policy.rules:
            if rule.resource_type == resource_type:
                exact = rule
            elif rule.resource_type == "*":
                wildcard = rule
        return exact or wildcard

    # ── Primary interface ──────────────────────────────────────────────────

    def can_access(
        self,
        policy: EffectiveAccessPolicy,
        resource_type: str,
        interaction: str,
        resource: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Return True if *interaction* on *resource_type* is permitted by *policy*.

        Args:
            policy:        Effective policy for the current user/request.
            resource_type: FHIR resource type, e.g. 'Patient'.
            interaction:   One of: search, read, create, update, delete.
            resource:      The FHIR resource dict (required for criteria checks).
        """
        # Admin bypass
        if policy.is_admin:
            return True

        rule = self._find_rule(policy, resource_type)
        if rule is None:
            logger.debug("access.denied resource_type=%s — no matching rule", resource_type)
            return False

        # readonly block on writes
        if rule.readonly and interaction in _WRITE_INTERACTIONS:
            logger.debug("access.denied interaction=%s — rule.readonly=True", interaction)
            return False

        # Interaction allowlist check
        if rule.interaction is not None and interaction not in rule.interaction:
            logger.debug(
                "access.denied interaction=%s not in %s", interaction, rule.interaction
            )
            return False

        # Criteria check (resource-level, requires actual resource)
        if rule.criteria and resource is not None:
            if not self._check_criteria(rule.criteria, resource):
                logger.debug(
                    "access.denied resource=%s/%s — criteria mismatch",
                    resource.get("resourceType"),
                    resource.get("id"),
                )
                return False

        return True

    # ── Field filtering ────────────────────────────────────────────────────

    def filter_fields(
        self,
        policy: EffectiveAccessPolicy,
        resource_type: str,
        resource: dict[str, Any],
    ) -> dict[str, Any]:
        """Return *resource* with hidden fields removed.

        Returns an empty dict if no rule matches (deny-by-default).
        """
        if policy.is_admin:
            return dict(resource)

        rule = self._find_rule(policy, resource_type)
        if rule is None:
            return {}

        filtered = dict(resource)
        for field in rule.hidden_fields or []:
            filtered.pop(field, None)

        return filtered

    def get_readonly_fields(
        self, policy: EffectiveAccessPolicy, resource_type: str
    ) -> list[str]:
        """Return list of field names that are read-only for this resource type."""
        if policy.is_admin:
            return []

        rule = self._find_rule(policy, resource_type)
        if rule is None:
            return []

        fields = list(rule.readonly_fields or [])
        if rule.readonly:
            # entire resource is read-only — signal caller
            fields.append("__all__")
        return fields

    # ── Criteria helper ────────────────────────────────────────────────────

    def _check_criteria(self, criteria: str, resource: dict[str, Any]) -> bool:
        """Use FHIRCriteriaMatcher if available; otherwise skip criteria check."""
        try:
            from intellicare_core.subscriptions.matcher import (  # noqa: PLC0415
                FHIRCriteriaMatcher,
            )

            matcher = FHIRCriteriaMatcher(criteria)
            return matcher.matches(resource)
        except Exception:
            # If matcher not available or criteria malformed → allow access
            return True
