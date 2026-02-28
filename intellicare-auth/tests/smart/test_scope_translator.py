"""Tests for SMART scope translator — 20 scenarios."""

import pytest

from intellicare_auth.smart.scope_translator import (
    parse_smart_scopes,
    smart_scopes_to_rules,
)


# ── parse_smart_scopes ────────────────────────────────────────────────────────


def test_parse_patient_read() -> None:
    result = parse_smart_scopes("patient/Patient.read")
    assert ("patient", "Patient", "read") in result


def test_parse_user_write() -> None:
    result = parse_smart_scopes("user/Observation.write")
    assert ("user", "Observation", "write") in result


def test_parse_system_star() -> None:
    result = parse_smart_scopes("system/Patient.*")
    assert ("system", "Patient", "*") in result


def test_parse_wildcard_resource() -> None:
    result = parse_smart_scopes("patient/*.read")
    assert ("patient", "*", "read") in result


def test_parse_multiple_scopes() -> None:
    result = parse_smart_scopes("patient/Patient.read user/Observation.write system/Patient.*")
    assert len(result) == 3


def test_parse_non_smart_ignored() -> None:
    result = parse_smart_scopes("openid fhirUser offline_access")
    assert result == []


def test_parse_mixed_valid_invalid() -> None:
    result = parse_smart_scopes("openid patient/Patient.read fhirUser")
    assert len(result) == 1
    assert result[0] == ("patient", "Patient", "read")


def test_parse_empty_string() -> None:
    assert parse_smart_scopes("") == []


def test_parse_lowercase_resource_ignored() -> None:
    # 'patient' starts lowercase — not a valid FHIR resource
    result = parse_smart_scopes("patient/patient.read")
    assert result == []


# ── smart_scopes_to_rules ─────────────────────────────────────────────────────


def test_read_scope_grants_read_interactions() -> None:
    rules = smart_scopes_to_rules("patient/Patient.read")
    patient_rule = next((r for r in rules if r["resource_type"] == "Patient"), None)
    assert patient_rule is not None
    assert "read" in patient_rule["interaction"]
    assert "search" in patient_rule["interaction"]


def test_read_scope_does_not_grant_write() -> None:
    rules = smart_scopes_to_rules("patient/Patient.read")
    patient_rule = next(r for r in rules if r["resource_type"] == "Patient")
    assert "create" not in patient_rule["interaction"]
    assert "update" not in patient_rule["interaction"]
    assert "delete" not in patient_rule["interaction"]


def test_write_scope_grants_write_interactions() -> None:
    rules = smart_scopes_to_rules("patient/Patient.write")
    patient_rule = next(r for r in rules if r["resource_type"] == "Patient")
    assert "create" in patient_rule["interaction"]
    assert "update" in patient_rule["interaction"]


def test_write_scope_does_not_grant_read() -> None:
    rules = smart_scopes_to_rules("patient/Patient.write")
    patient_rule = next(r for r in rules if r["resource_type"] == "Patient")
    assert "read" not in patient_rule["interaction"]


def test_star_scope_grants_all_interactions() -> None:
    rules = smart_scopes_to_rules("patient/Patient.*")
    patient_rule = next(r for r in rules if r["resource_type"] == "Patient")
    assert "read" in patient_rule["interaction"]
    assert "create" in patient_rule["interaction"]
    assert "delete" in patient_rule["interaction"]


def test_wildcard_resource_expands_to_allowed_types() -> None:
    rules = smart_scopes_to_rules(
        "patient/*.read",
        allowed_resource_types=["Patient", "Observation"],
    )
    rts = {r["resource_type"] for r in rules}
    assert "Patient" in rts
    assert "Observation" in rts


def test_wildcard_resource_without_allowed_types_uses_sentinel() -> None:
    rules = smart_scopes_to_rules("patient/*.read")
    rts = {r["resource_type"] for r in rules}
    assert "*" in rts


def test_multiple_scopes_merged() -> None:
    rules = smart_scopes_to_rules("patient/Patient.read patient/Patient.write")
    patient_rule = next(r for r in rules if r["resource_type"] == "Patient")
    # Should have both read and write interactions
    assert "read" in patient_rule["interaction"]
    assert "create" in patient_rule["interaction"]


def test_resource_not_in_allowed_list_excluded() -> None:
    rules = smart_scopes_to_rules(
        "patient/Observation.read",
        allowed_resource_types=["Patient"],
    )
    rts = {r["resource_type"] for r in rules}
    assert "Observation" not in rts


def test_empty_scope_returns_empty_rules() -> None:
    assert smart_scopes_to_rules("") == []
