"""Tests for smart_scopes — 20 scenarios."""

import pytest

from intellicare_core.access.models import EffectiveAccessPolicy, ResourceRule
from intellicare_core.access.smart_scopes import (
    apply_smart_scopes,
    parse_smart_scopes,
)


def _policy(*rules: ResourceRule) -> EffectiveAccessPolicy:
    return EffectiveAccessPolicy(rules=list(rules))


def _rule(resource_type: str, interaction=None) -> ResourceRule:
    return ResourceRule(resource_type=resource_type, interaction=interaction)


# ── parse_smart_scopes ────────────────────────────────────────────────────────


def test_parse_patient_read() -> None:
    parsed = parse_smart_scopes("patient/Patient.read")
    assert ("patient", "Patient", "read") in parsed


def test_parse_user_write() -> None:
    parsed = parse_smart_scopes("user/Observation.write")
    assert ("user", "Observation", "write") in parsed


def test_parse_system_all() -> None:
    parsed = parse_smart_scopes("system/Patient.*")
    assert ("system", "Patient", "*") in parsed


def test_parse_wildcard_resource() -> None:
    parsed = parse_smart_scopes("patient/*.read")
    assert ("patient", "*", "read") in parsed


def test_parse_multiple_scopes() -> None:
    parsed = parse_smart_scopes("patient/Patient.read user/Observation.write system/Patient.*")
    assert len(parsed) == 3


def test_parse_unknown_scope_skipped() -> None:
    parsed = parse_smart_scopes("openid profile email")
    assert parsed == []


def test_parse_mixed_valid_invalid() -> None:
    parsed = parse_smart_scopes("openid patient/Patient.read fhirUser")
    assert len(parsed) == 1
    assert parsed[0] == ("patient", "Patient", "read")


def test_parse_empty_string() -> None:
    assert parse_smart_scopes("") == []


# ── apply_smart_scopes ────────────────────────────────────────────────────────


def test_apply_none_scopes_returns_unchanged() -> None:
    policy = _policy(_rule("Patient", ["read", "create"]))
    result = apply_smart_scopes(policy, None)
    assert result.rules == policy.rules


def test_apply_empty_string_returns_unchanged() -> None:
    policy = _policy(_rule("Patient", ["read", "create"]))
    result = apply_smart_scopes(policy, "")
    assert result.rules == policy.rules


def test_apply_read_scope_removes_write_interactions() -> None:
    policy = _policy(_rule("Patient", ["search", "read", "create", "update"]))
    result = apply_smart_scopes(policy, "patient/Patient.read")
    rule = next(r for r in result.rules if r.resource_type == "Patient")
    assert "search" in rule.interaction
    assert "read" in rule.interaction
    assert "create" not in rule.interaction
    assert "update" not in rule.interaction


def test_apply_write_scope_removes_read_interactions() -> None:
    policy = _policy(_rule("Patient", ["search", "read", "create"]))
    result = apply_smart_scopes(policy, "patient/Patient.write")
    rule = next(r for r in result.rules if r.resource_type == "Patient")
    assert "create" in rule.interaction
    assert "search" not in rule.interaction
    assert "read" not in rule.interaction


def test_apply_star_scope_preserves_all() -> None:
    policy = _policy(_rule("Patient", ["search", "read", "create", "delete"]))
    result = apply_smart_scopes(policy, "patient/Patient.*")
    rule = next(r for r in result.rules if r.resource_type == "Patient")
    assert set(rule.interaction) == {"search", "read", "create", "delete"}


def test_apply_scope_excludes_ungranted_resource_type() -> None:
    """SMART scope for Patient.read should not grant Observation access."""
    policy = _policy(
        _rule("Patient", ["read"]),
        _rule("Observation", ["read", "create"]),
    )
    result = apply_smart_scopes(policy, "patient/Patient.read")
    resource_types = {r.resource_type for r in result.rules}
    assert "Patient" in resource_types
    assert "Observation" not in resource_types


def test_apply_wildcard_resource_grants_any_type() -> None:
    """patient/*.read should grant read on all resource types in policy."""
    policy = _policy(
        _rule("Patient", ["read", "create"]),
        _rule("Observation", ["read", "create"]),
    )
    result = apply_smart_scopes(policy, "patient/*.read")
    assert len(result.rules) == 2
    for rule in result.rules:
        assert "read" in rule.interaction
        assert "create" not in rule.interaction


def test_apply_preserves_other_rule_attributes() -> None:
    """hidden_fields, readonly_fields, criteria should be preserved."""
    policy = _policy(
        ResourceRule(
            resource_type="Patient",
            interaction=["read", "create"],
            hidden_fields=["meta"],
            readonly_fields=["status"],
            criteria="Patient?active=true",
            readonly=False,
        )
    )
    result = apply_smart_scopes(policy, "patient/Patient.read")
    rule = result.rules[0]
    assert rule.hidden_fields == ["meta"]
    assert rule.readonly_fields == ["status"]
    assert rule.criteria == "Patient?active=true"


def test_apply_no_intersection_removes_rule() -> None:
    """Policy read-only, SMART wants write-only → empty intersection → no rule."""
    policy = _policy(_rule("Patient", ["read", "search"]))
    result = apply_smart_scopes(policy, "patient/Patient.write")
    assert not any(r.resource_type == "Patient" for r in result.rules)


def test_apply_preserves_admin_flag() -> None:
    policy = EffectiveAccessPolicy(
        rules=[_rule("Patient", ["read"])],
        is_admin=True,
    )
    result = apply_smart_scopes(policy, "patient/Patient.read")
    assert result.is_admin is True
