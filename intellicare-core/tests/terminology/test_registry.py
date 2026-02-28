"""Tests for TerminologyRegistry — 18 scenarios."""

import pytest

from intellicare_core.terminology.registry import (
    ICD10_SYSTEM,
    LOINC_SYSTEM,
    RXNORM_SYSTEM,
    SNOMED_SYSTEM,
    TUSS_SYSTEM,
    TerminologyRegistry,
)
from intellicare_core.terminology.models import CodeSystemConcept


@pytest.fixture
def reg() -> TerminologyRegistry:
    return TerminologyRegistry()


# ── Concept lookup ─────────────────────────────────────────────────────────────


def test_lookup_known_loinc(reg: TerminologyRegistry) -> None:
    concept = reg.get_concept(LOINC_SYSTEM, "8867-4")
    assert concept is not None
    assert concept.display == "Heart rate"
    assert concept.system == LOINC_SYSTEM


def test_lookup_known_icd10(reg: TerminologyRegistry) -> None:
    concept = reg.get_concept(ICD10_SYSTEM, "E11")
    assert concept is not None
    assert "Diabetes" in concept.display


def test_lookup_known_snomed(reg: TerminologyRegistry) -> None:
    concept = reg.get_concept(SNOMED_SYSTEM, "38341003")
    assert concept is not None
    assert "Hypertensive" in concept.display


def test_lookup_known_tuss(reg: TerminologyRegistry) -> None:
    concept = reg.get_concept(TUSS_SYSTEM, "40901013")
    assert concept is not None
    assert "Hemograma" in concept.display


def test_lookup_known_rxnorm_has_designation(reg: TerminologyRegistry) -> None:
    concept = reg.get_concept(RXNORM_SYSTEM, "860975")
    assert concept is not None
    assert "pt-BR" in concept.designations
    assert "etformina" in concept.designations["pt-BR"]


def test_lookup_unknown_returns_none(reg: TerminologyRegistry) -> None:
    assert reg.get_concept(LOINC_SYSTEM, "99999-9") is None


def test_lookup_wrong_system_returns_none(reg: TerminologyRegistry) -> None:
    assert reg.get_concept("http://unknown.example.com", "E11") is None


def test_loinc_concept_has_properties(reg: TerminologyRegistry) -> None:
    concept = reg.get_concept(LOINC_SYSTEM, "4548-4")
    assert concept is not None
    assert concept.properties.get("class") == "CHEM"
    assert concept.properties.get("scale") == "Qn"


def test_icd10_concept_has_parent(reg: TerminologyRegistry) -> None:
    concept = reg.get_concept(ICD10_SYSTEM, "N18.3")
    assert concept is not None
    assert concept.parent == "N18"


def test_total_concepts_populated(reg: TerminologyRegistry) -> None:
    assert reg.total_concepts >= 60  # LOINC(20) + ICD10(21) + SNOMED(10) + TUSS(10) + RxNorm(10)


# ── ValueSet expand ────────────────────────────────────────────────────────────


def test_expand_vital_signs(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    expansion = reg.expand_value_set(url)
    assert expansion is not None
    assert expansion.total >= 8
    codes = {c.code for c in expansion.concepts}
    assert "8867-4" in codes  # heart rate
    assert "55284-4" in codes  # blood pressure


def test_expand_chronic_conditions(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/chronic-conditions-icd10"
    expansion = reg.expand_value_set(url)
    assert expansion is not None
    codes = {c.code for c in expansion.concepts}
    assert "N18" in codes
    assert "E11" in codes


def test_expand_unknown_url_returns_none(reg: TerminologyRegistry) -> None:
    assert reg.expand_value_set("http://unknown.example.com/ValueSet/foo") is None


# ── ValueSet validate_code ─────────────────────────────────────────────────────


def test_validate_code_present(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    assert reg.validate_code_in_value_set(url, LOINC_SYSTEM, "8867-4") is True


def test_validate_code_absent(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    assert reg.validate_code_in_value_set(url, LOINC_SYSTEM, "9999-0") is False


def test_validate_code_wrong_system(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ValueSet/vital-signs"
    assert reg.validate_code_in_value_set(url, ICD10_SYSTEM, "8867-4") is False


# ── ConceptMap translate ───────────────────────────────────────────────────────


def test_translate_icd10_to_snomed_found(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ConceptMap/icd10-to-snomed"
    matches = reg.translate(url, ICD10_SYSTEM, "E11")
    assert len(matches) == 1
    assert matches[0]["target_code"] == "44054006"
    assert matches[0]["equivalence"] == "equivalent"


def test_translate_unknown_code_returns_empty(reg: TerminologyRegistry) -> None:
    url = "http://intellicare.example.com/fhir/ConceptMap/icd10-to-snomed"
    assert reg.translate(url, ICD10_SYSTEM, "Z99.9") == []


def test_translate_unknown_map_returns_empty(reg: TerminologyRegistry) -> None:
    assert reg.translate("http://x/ConceptMap/unknown", ICD10_SYSTEM, "E11") == []
