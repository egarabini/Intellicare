"""PolicyBuilder — compose an EffectiveAccessPolicy from multiple memberships.

Uses injectable async callables (MembershipFetcher + PolicyFetcher) to remain
decoupled from SQLAlchemy. In production, Grahame provides concrete implementations.
"""

from __future__ import annotations

import logging
import re
from typing import Awaitable, Callable, Optional

from .models import (
    AccessPolicyRecord,
    EffectiveAccessPolicy,
    ResourceRule,
    TenantMembershipRecord,
)
from .smart_scopes import apply_smart_scopes

logger = logging.getLogger(__name__)

# Injectable callables
MembershipFetcher = Callable[
    [str, str], Awaitable[list[TenantMembershipRecord]]
]
"""async (tenant_id, user_id) → list[TenantMembershipRecord]"""

PolicyFetcher = Callable[
    [str], Awaitable[Optional[AccessPolicyRecord]]
]
"""async (policy_id) → AccessPolicyRecord | None"""

# Parameter substitution pattern: %param_name
_PARAM_RE = re.compile(r"%([a-zA-Z_][a-zA-Z0-9_]*)")


def _substitute_parameters(value: str, parameters: dict[str, str]) -> str:
    """Replace %param_name placeholders in *value* with values from *parameters*."""
    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        return parameters.get(m.group(0), m.group(0))
    return _PARAM_RE.sub(_replace, value)


def _apply_parameters_to_rule(rule: ResourceRule, parameters: dict[str, str]) -> ResourceRule:
    """Return a copy of *rule* with parameter substitutions applied to criteria."""
    if not parameters or not rule.criteria:
        return rule
    return ResourceRule(
        resource_type=rule.resource_type,
        interaction=rule.interaction,
        criteria=_substitute_parameters(rule.criteria, parameters),
        readonly=rule.readonly,
        readonly_fields=rule.readonly_fields,
        hidden_fields=rule.hidden_fields,
    )


class PolicyBuilder:
    """Compose an EffectiveAccessPolicy from all memberships of a user.

    Inject *membership_fetcher* and *policy_fetcher* at construction time or
    pass them to :meth:`build_effective_policy` directly.
    """

    def __init__(
        self,
        membership_fetcher: Optional[MembershipFetcher] = None,
        policy_fetcher: Optional[PolicyFetcher] = None,
    ) -> None:
        self._membership_fetcher = membership_fetcher
        self._policy_fetcher = policy_fetcher

    async def build_effective_policy(
        self,
        tenant_id: str,
        user_id: str,
        smart_scopes: Optional[str] = None,
        *,
        membership_fetcher: Optional[MembershipFetcher] = None,
        policy_fetcher: Optional[PolicyFetcher] = None,
    ) -> EffectiveAccessPolicy:
        """Compose all AccessPolicies assigned to *user_id* in *tenant_id*.

        1. Fetch all TenantMembership records for the user.
        2. For each membership, load its AccessPolicy.
        3. Apply parameter substitutions.
        4. Union all ResourceRules.
        5. Optionally restrict by SMART scopes.

        Args:
            tenant_id:          Tenant identifier.
            user_id:            User identifier (Keycloak sub claim).
            smart_scopes:       Space-separated SMART scope string (optional).
            membership_fetcher: Override the instance-level fetcher (optional).
            policy_fetcher:     Override the instance-level policy fetcher (optional).

        Returns:
            EffectiveAccessPolicy with combined rules.
        """
        _mf = membership_fetcher or self._membership_fetcher
        _pf = policy_fetcher or self._policy_fetcher

        if _mf is None:
            raise RuntimeError("PolicyBuilder: membership_fetcher is not configured")
        if _pf is None:
            raise RuntimeError("PolicyBuilder: policy_fetcher is not configured")

        memberships: list[TenantMembershipRecord] = await _mf(tenant_id, user_id)

        is_admin = any(m.is_admin for m in memberships)
        all_rules: list[ResourceRule] = []
        compartment_ref: Optional[str] = None

        for membership in memberships:
            if membership.access_policy_id is None:
                continue

            policy = await _pf(membership.access_policy_id)
            if policy is None:
                logger.warning(
                    "policy_builder.missing_policy policy_id=%s user=%s",
                    membership.access_policy_id,
                    user_id,
                )
                continue

            parameters: dict[str, str] = {}
            if membership.parameters:
                parameters = {
                    k: v for k, v in membership.parameters.items() if isinstance(v, str)
                }

            for rule in policy.resource_rules:
                all_rules.append(_apply_parameters_to_rule(rule, parameters))

            # Take compartment from first policy that defines one
            if compartment_ref is None:
                compartment_ref = policy.compartment_ref

        effective = EffectiveAccessPolicy(
            rules=all_rules,
            is_admin=is_admin,
            compartment_ref=compartment_ref,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        if smart_scopes:
            effective = apply_smart_scopes(effective, smart_scopes)

        logger.debug(
            "policy_builder.composed user=%s tenant=%s rules=%d admin=%s",
            user_id,
            tenant_id,
            len(effective.rules),
            is_admin,
        )
        return effective
