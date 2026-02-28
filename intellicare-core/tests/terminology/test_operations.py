"""Tests for terminology operations ($lookup, $expand, $validate-code, $translate) — 17 scenarios."""

import pytest

from intellicare_core.terminology.registry import (
    ICD10_SYSTEM,
    LOINC_SYSTEM,
    SNOMED_SYSTEM,
    TerminologyRegistry,
)
from intellicare_core.terminology.operations import (
    expand,
    lookup,
    translate,
    validate_code,
)


@pytest.fixture
def reg() -> TerminologyRegistry:
    return TerminologyRegistry()


# ── lookup ─────────────────────────────────────────────────────────────────────


def test_lookup_returns_parameters_resource(reg: TerminologyRegistry) -> None:
    result = lookup(LOINC_SYSTEM, "8867-4", registry=reg)
    assert result is not None
    assert result["resourceType"] == "Parameters"
    assert "parameter" in result


def test_lookup_contains_display(reg: TerminologyRegistry) -> None:
    result = lookup(LOINC_SYSTEM, "8867-4", registry=reg)
    assert result is not None
    params = {p["name"]: p for p in result["parameter"]}
    assert "display" in params
    assert params["display"]["valueString"] == "Heart rate"


def test_lookup_contains_definition(reg: TerminologyRegistry) -> None:
    result = lookup(LOINC_SYSTEM, "8867-4", registry=reg)
    assert result is not None
    names = [p["name"] for p in result["parameter"]]
    assert "definition" in names


def test_lookup_rxnorm_has_designation(reg: TerminologyRegistry) -> None:
    from intellicare_core.terminology.registry import RXNORM_SYSTEM
    result = lookup(RXNORM_SYSTEM, "860975", registry=reg)
    assert result is not None
    names = [p["name"] for p in result["parameter"]]
    assert "designation" in names


def test_lookup_loinc_has_property(reg: TerminologyRegistry) -> None:
    result = lookup(LOINC_SYSTEM, "4548-4", registry=reg)
    assert result is not None
    names = [p["name"] for p in result["parameter"]]
    assert "property" in names


def test_lookup_unknown_returns_none(reg: TerminologyRegistry) -> None:
    assert lookup(LOINC_SYSTEM, "0000-0", registry=reg) is None


# ── expand ─────────────────────────────────────────────────────────────────────


def test_expand_returns_valueset_resource(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    result = expand(url, registry=reg)
    assert result is not None
    assert result["resourceType"] == "ValueSet"
    assert "expansion" in result


def test_expand_contains_list(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    result = expand(url, registry=reg)
    assert result is not None
    contains = result["expansion"]["contains"]
    assert len(contains) >= 8
    codes = {c["code"] for c in contains}
    assert "8867-4" in codes


def test_expand_pagination(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    result = expand(url, registry=reg, offset=0, count=3)
    assert result is not None
    assert len(result["expansion"]["contains"]) <= 3
    assert result["expansion"]["offset"] == 0


def test_expand_unknown_url_returns_none(reg: TerminologyRegistry) -> None:
    assert expand("http://x/ValueSet/unknown", registry=reg) is None


# ── validate_code ──────────────────────────────────────────────────────────────


def test_validate_code_valid_returns_true(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    result = validate_code(url, LOINC_SYSTEM, "8867-4", registry=reg)
    params = {p["name"]: p for p in result["parameter"]}
    assert params["result"]["valueBoolean"] is True
    assert "display" in params


def test_validate_code_invalid_returns_false(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    result = validate_code(url, LOINC_SYSTEM, "9999-9", registry=reg)
    params = {p["name"]: p for p in result["parameter"]}
    assert params["result"]["valueBoolean"] is False
    assert "message" in params


def test_validate_code_wrong_system_returns_false(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    result = validate_code(url, ICD10_SYSTEM, "8867-4", registry=reg)
    params = {p["name"]: p for p in result["parameter"]}
    assert params["result"]["valueBoolean"] is False


# ── translate ──────────────────────────────────────────────────────────────────


def test_translate_found_returns_result_true(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ConceptMap/icd10-to-snomed"
    result = translate(url, ICD10_SYSTEM, "N18", registry=reg)
    params_by_name = [p["name"] for p in result["parameter"]]
    assert "result" in params_by_name
    assert "match" in params_by_name
    result_param = next(p for p in result["parameter"] if p["name"] == "result")
    assert result_param["valueBoolean"] is True


def test_translate_match_contains_target_concept(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ConceptMap/icd10-to-snomed"
    result = translate(url, ICD10_SYSTEM, "E11", registry=reg)
    match_param = next(p for p in result["parameter"] if p["name"] == "match")
    concept_part = next(p for p in match_param["part"] if p["name"] == "concept")
    assert concept_part["valueCoding"]["code"] == "44054006"
    assert concept_part["valueCoding"]["system"] == SNOMED_SYSTEM


def test_translate_not_found_returns_result_false(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ConceptMap/icd10-to-snomed"
    result = translate(url, ICD10_SYSTEM, "Z99.9", registry=reg)
    result_param = next(p for p in result["parameter"] if p["name"] == "result")
    assert result_param["valueBoolean"] is False


def test_translate_unknown_map_returns_result_false(reg: TerminologyRegistry) -> None:
    result = translate("http://x/ConceptMap/none", ICD10_SYSTEM, "E11", registry=reg)
    result_param = next(p for p in result["parameter"] if p["name"] == "result")
    assert result_param["valueBoolean"] is False
