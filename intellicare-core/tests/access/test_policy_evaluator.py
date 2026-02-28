"""Tests for PolicyEvaluator — 28 scenarios."""

import pytest

from intellicare_core.access.models import EffectiveAccessPolicy, ResourceRule
from intellicare_core.access.policy_evaluator import PolicyEvaluator


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def ev() -> PolicyEvaluator:
    return PolicyEvaluator()


def _policy(*rules: ResourceRule, is_admin: bool = False) -> EffectiveAccessPolicy:
    return EffectiveAccessPolicy(rules=list(rules), is_admin=is_admin)


def _rule(
    resource_type: str,
    interaction=None,
    *,
    readonly: bool = False,
    criteria: str | None = None,
    hidden_fields: list[str] | None = None,
    readonly_fields: list[str] | None = None,
) -> ResourceRule:
    return ResourceRule(
        resource_type=resource_type,
        interaction=interaction,
        readonly=readonly,
        criteria=criteria,
        hidden_fields=hidden_fields,
        readonly_fields=readonly_fields,
    )


PATIENT = {"resourceType": "Patient", "id": "p-001", "active": True}


# ── Admin bypass ─────────────────────────────────────────────────────────────


def test_admin_can_do_anything(ev: PolicyEvaluator) -> None:
    policy = _policy(is_admin=True)
    assert ev.can_access(policy, "Patient", "delete") is True
    assert ev.can_access(policy, "Bot", "create") is True


def test_admin_filter_fields_returns_full_resource(ev: PolicyEvaluator) -> None:
    policy = _policy(is_admin=True)
    r = ev.filter_fields(policy, "Patient", PATIENT)
    assert r == PATIENT


# ── No rule → deny ────────────────────────────────────────────────────────────


def test_no_rule_denies_access(ev: PolicyEvaluator) -> None:
    policy = _policy()
    assert ev.can_access(policy, "Patient", "read") is False


def test_no_rule_filter_fields_returns_empty(ev: PolicyEvaluator) -> None:
    policy = _policy()
    r = ev.filter_fields(policy, "Patient", PATIENT)
    assert r == {}


# ── Exact resource type match ─────────────────────────────────────────────────


def test_exact_match_allows_listed_interaction(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("Patient", ["read", "search"]))
    assert ev.can_access(policy, "Patient", "read") is True
    assert ev.can_access(policy, "Patient", "search") is True


def test_exact_match_denies_unlisted_interaction(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("Patient", ["read"]))
    assert ev.can_access(policy, "Patient", "create") is False
    assert ev.can_access(policy, "Patient", "delete") is False


# ── Wildcard resource type ────────────────────────────────────────────────────


def test_wildcard_rule_matches_any_resource(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("*", ["read", "search"]))
    assert ev.can_access(policy, "Patient", "read") is True
    assert ev.can_access(policy, "Observation", "read") is True


def test_exact_rule_takes_precedence_over_wildcard(ev: PolicyEvaluator) -> None:
    wildcard = _rule("*", ["read"])
    exact = _rule("Patient", ["read", "create"])
    policy = _policy(wildcard, exact)
    # Patient has exact rule that allows create
    assert ev.can_access(policy, "Patient", "create") is True
    # Observation uses wildcard — no create
    assert ev.can_access(policy, "Observation", "create") is False


# ── Readonly flag ─────────────────────────────────────────────────────────────


def test_readonly_rule_denies_write_interactions(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("MedicationRequest", readonly=True))
    for interaction in ("create", "update", "delete"):
        assert ev.can_access(policy, "MedicationRequest", interaction) is False


def test_readonly_rule_allows_read_interactions(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("MedicationRequest", readonly=True))
    assert ev.can_access(policy, "MedicationRequest", "read") is True
    assert ev.can_access(policy, "MedicationRequest", "search") is True


# ── Interaction list = None → all allowed ─────────────────────────────────────


def test_none_interaction_allows_everything(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("Patient", None))
    for interaction in ("search", "read", "create", "update", "delete"):
        assert ev.can_access(policy, "Patient", interaction) is True


# ── filter_fields ─────────────────────────────────────────────────────────────


def test_filter_fields_removes_hidden(ev: PolicyEvaluator) -> None:
    resource = {"resourceType": "Patient", "id": "p-1", "meta": {"versionId": "1"}}
    policy = _policy(_rule("Patient", None, hidden_fields=["meta"]))
    filtered = ev.filter_fields(policy, "Patient", resource)
    assert "meta" not in filtered
    assert filtered["id"] == "p-1"


def test_filter_fields_no_hidden_returns_copy(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("Patient", None))
    filtered = ev.filter_fields(policy, "Patient", PATIENT)
    assert filtered == PATIENT
    assert filtered is not PATIENT  # copy


def test_filter_fields_multiple_hidden(ev: PolicyEvaluator) -> None:
    resource = {"resourceType": "Obs", "id": "o-1", "meta": {}, "text": "note", "status": "final"}
    policy = _policy(_rule("Obs", None, hidden_fields=["meta", "text"]))
    filtered = ev.filter_fields(policy, "Obs", resource)
    assert "meta" not in filtered
    assert "text" not in filtered
    assert "status" in filtered


# ── get_readonly_fields ────────────────────────────────────────────────────────


def test_get_readonly_fields_returns_list(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("Observation", None, readonly_fields=["status", "category"]))
    fields = ev.get_readonly_fields(policy, "Observation")
    assert "status" in fields
    assert "category" in fields


def test_get_readonly_fields_includes_all_marker_if_readonly(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("Observation", readonly=True, readonly_fields=["code"]))
    fields = ev.get_readonly_fields(policy, "Observation")
    assert "__all__" in fields


def test_get_readonly_fields_empty_for_admin(ev: PolicyEvaluator) -> None:
    policy = _policy(is_admin=True)
    assert ev.get_readonly_fields(policy, "Patient") == []


def test_get_readonly_fields_empty_when_no_rule(ev: PolicyEvaluator) -> None:
    policy = _policy()
    assert ev.get_readonly_fields(policy, "Patient") == []


# ── Criteria matching ─────────────────────────────────────────────────────────


def test_criteria_match_allows_access(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("Patient", ["read"], criteria="Patient?active=true"))
    resource = {"resourceType": "Patient", "id": "p-1", "active": True}
    assert ev.can_access(policy, "Patient", "read", resource) is True


def test_criteria_mismatch_denies_access(ev: PolicyEvaluator) -> None:
    policy = _policy(_rule("Patient", ["read"], criteria="Patient?active=false"))
    resource = {"resourceType": "Patient", "id": "p-1", "active": True}
    assert ev.can_access(policy, "Patient", "read", resource) is False


def test_criteria_not_checked_without_resource(ev: PolicyEvaluator) -> None:
    """If no resource is provided, criteria check is skipped → allow."""
    policy = _policy(_rule("Patient", ["read"], criteria="Patient?status=active"))
    assert ev.can_access(policy, "Patient", "read") is True


# ── Composite policy ──────────────────────────────────────────────────────────


def test_composite_policy_multiple_rules(ev: PolicyEvaluator) -> None:
    policy = _policy(
        _rule("Patient", ["read", "search"]),
        _rule("Observation", ["read", "search", "create"]),
    )
    assert ev.can_access(policy, "Patient", "read") is True
    assert ev.can_access(policy, "Patient", "create") is False
    assert ev.can_access(policy, "Observation", "create") is True
    assert ev.can_access(policy, "Observation", "delete") is False
    assert ev.can_access(policy, "MedicationRequest", "read") is False
