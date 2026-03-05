"""PolicyEvaluator — decides whether an operation is allowed by an AccessPolicy.
Adheres to the W2-B Medplum Integration Spec.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, List, Dict

logger = logging.getLogger(__name__)

# Constants for standard FHIR interactions
_WRITE_INTERACTIONS = frozenset({"create", "update", "delete", "patch"})
_READ_INTERACTIONS = frozenset({"read", "search"})


@dataclass
class EvaluationResult:
    """Standardized result for a policy evaluation."""
    allowed: bool
    reason: str
    matched_rule: Optional[Dict[str, Any]] = None


class PolicyEvaluator:
    """Stateless evaluator — instantiate once and reuse."""

    def _find_matching_rules(
        self, policy: dict, resource_type: str
    ) -> List[Dict[str, Any]]:
        """Find rules matching the resource_type or wildcard '*'."""
        rules = policy.get("resource_rules", [])
        
        # In case the DB structure is a list of Pydantic models, extract dicts
        # (Handling both dict-based and model-based inputs safely)
        if rules and not isinstance(rules[0], dict):
            rules = [r.dict() if hasattr(r, 'dict') else r for r in rules]
            
        matched = []
        for rule in rules:
            rt = rule.get("resource_type")
            if rt == resource_type or rt == "*":
                matched.append(rule)
        return matched

    def _check_criteria(self, criteria: str, resource: dict[str, Any]) -> bool:
        """Use FHIRCriteriaMatcher to validate resource criteria."""
        try:
            from intellicare_core.subscriptions.matcher import FHIRCriteriaMatcher
            matcher = FHIRCriteriaMatcher(criteria)
            return matcher.matches(resource)
        except Exception as e:
            logger.warning(f"Criteria evaluation failed for {criteria}: {e}")
            return False  # Fail closed if criteria is malformed

    def can_read(
        self,
        policy: dict,
        resource_type: str,
        resource: Optional[dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Evaluate if the user can read or search the given resource type."""
        return self._evaluate(policy, resource_type, "read", resource)

    def can_write(
        self,
        policy: dict,
        resource_type: str,
        interaction: str,
        resource: Optional[dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Evaluate if the user can create, update, or delete the resource."""
        if interaction not in _WRITE_INTERACTIONS:
            return EvaluationResult(False, f"Invalid write interaction: {interaction}")
        return self._evaluate(policy, resource_type, interaction, resource)

    def _evaluate(
        self,
        policy: dict,
        resource_type: str,
        interaction: str,
        resource: Optional[dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Core first-match-wins evaluation logic."""
        
        # 1. Admin bypass
        if policy.get("is_admin", False):
            return EvaluationResult(True, "Admin bypass")

        rules = self._find_matching_rules(policy, resource_type)
        if not rules:
            return EvaluationResult(False, f"No matching rule for resource_type '{resource_type}'")

        for rule in rules:
            # Check interaction
            interactions = rule.get("interaction", [])
            
            # Interpret empty list or None as 'no interactions allowed' by this rule,
            # or interpret wildcard
            if interactions != ["*"] and interaction not in interactions:
                continue
                
            # Read-only enforcement for write interactions
            if interaction in _WRITE_INTERACTIONS and rule.get("readonly", False):
                continue
                
            # Criteria check
            criteria = rule.get("criteria")
            if criteria and resource is not None:
                if not self._check_criteria(criteria, resource):
                    continue
                    
            return EvaluationResult(True, "Rule matched", rule)

        # Deny by default if no rules matched the conditions completely
        return EvaluationResult(False, f"Interaction '{interaction}' denied by policy rules")

    def apply_field_restrictions(
        self,
        policy: dict,
        resource_type: str,
        resource: dict[str, Any],
    ) -> dict[str, Any]:
        """Return resource with hidden_fields removed."""
        if policy.get("is_admin", False):
            return dict(resource)

        # Find the first rule that matches and would allow 'read'.
        # Assuming if a rule allows read, we use its field restrictions.
        matched_result = self.can_read(policy, resource_type, resource)
        
        if not matched_result.allowed or not matched_result.matched_rule:
            return {} # Empty dict if access is completely denied

        rule = matched_result.matched_rule
        hidden_fields = rule.get("hidden_fields", [])
        
        if not hidden_fields:
            return dict(resource)
            
        filtered = dict(resource)
        for field in hidden_fields:
            filtered.pop(field, None)

        return filtered
