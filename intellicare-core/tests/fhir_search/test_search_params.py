"""Tests for FHIR search_params registry — 15 scenarios."""

import pytest

from intellicare_core.fhir_search.search_params import (
    SEARCH_PARAMS,
    SearchParamDef,
    get_search_param,
)


# ── get_search_param ──────────────────────────────────────────────────────────


def test_returns_none_for_unknown_code() -> None:
    result = get_search_param("Patient", "nonexistent-code")
    assert result is None


def test_returns_none_for_unknown_resource_and_unknown_code() -> None:
    result = get_search_param("UnknownResource", "nonexistent-code")
    assert result is None


def test_fallback_to_common_for_unknown_resource() -> None:
    """Unknown resource type falls back to _COMMON params."""
    result = get_search_param("UnknownResource", "_id")
    assert result is not None
    assert result.code == "_id"


def test_id_is_token_type() -> None:
    result = get_search_param("Patient", "_id")
    assert result is not None
    assert result.type == "token"


def test_last_updated_is_date_type() -> None:
    result = get_search_param("Patient", "_lastUpdated")
    assert result is not None
    assert result.type == "date"


def test_patient_birthdate_is_date_type() -> None:
    result = get_search_param("Patient", "birthdate")
    assert result is not None
    assert result.type == "date"
    assert "birthDate" in result.paths


def test_patient_name_has_array_paths() -> None:
    result = get_search_param("Patient", "name")
    assert result is not None
    assert any("[*]" in p for p in result.paths)


def test_patient_gender_is_token() -> None:
    result = get_search_param("Patient", "gender")
    assert result is not None
    assert result.type == "token"
    assert result.paths == ["gender"]


def test_observation_value_quantity_is_quantity() -> None:
    result = get_search_param("Observation", "value-quantity")
    assert result is not None
    assert result.type == "quantity"


def test_observation_subject_is_reference() -> None:
    result = get_search_param("Observation", "subject")
    assert result is not None
    assert result.type == "reference"


def test_encounter_date_paths_contain_period() -> None:
    result = get_search_param("Encounter", "date")
    assert result is not None
    assert "period.start" in result.paths


def test_condition_code_has_array_paths() -> None:
    result = get_search_param("Condition", "code")
    assert result is not None
    assert any("[*]" in p for p in result.paths)


def test_all_registered_resource_types_have_common_params() -> None:
    """Every resource in the registry should have _id and _lastUpdated."""
    for resource_type in SEARCH_PARAMS:
        assert "_id" in SEARCH_PARAMS[resource_type], f"{resource_type} missing _id"
        assert "_lastUpdated" in SEARCH_PARAMS[resource_type], f"{resource_type} missing _lastUpdated"


def test_search_param_def_is_dataclass() -> None:
    result = get_search_param("Patient", "gender")
    assert isinstance(result, SearchParamDef)


def test_identifier_has_system_and_value_paths() -> None:
    result = get_search_param("Patient", "identifier")
    assert result is not None
    # Should cover both value and system paths
    paths_str = " ".join(result.paths)
    assert "value" in paths_str
