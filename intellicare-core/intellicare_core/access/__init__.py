"""FHIR Access Policies — ABAC engine for IntelliCare.

Core package (Pydantic only — no SQLAlchemy).

Public API:
    - Models: ResourceRule, AccessPolicyRecord, TenantMembershipRecord, EffectiveAccessPolicy
    - PolicyEvaluator: can_access() + filter_fields()
    - PolicyBuilder: build_effective_policy()
    - FieldFilter: apply_hidden() + get_readonly_fields()
    - SmartScopes: apply_smart_scopes()
    - Compartment: CompartmentMatcher
"""

from .field_filter import FieldFilter
from .models import (
    AccessPolicyRecord,
    EffectiveAccessPolicy,
    ResourceRule,
    TenantMembershipRecord,
)
from .policy_builder import MembershipFetcher, PolicyBuilder, PolicyFetcher
from .policy_evaluator import PolicyEvaluator
from .smart_scopes import apply_smart_scopes, parse_smart_scopes

__all__ = [
    # Models
    "ResourceRule",
    "AccessPolicyRecord",
    "TenantMembershipRecord",
    "EffectiveAccessPolicy",
    # Evaluator
    "PolicyEvaluator",
    # Builder
    "PolicyBuilder",
    "MembershipFetcher",
    "PolicyFetcher",
    # Field filter
    "FieldFilter",
    # SMART scopes
    "apply_smart_scopes",
    "parse_smart_scopes",
]
