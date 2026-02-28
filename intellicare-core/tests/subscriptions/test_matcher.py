"""Tests for FHIRCriteriaMatcher — 25 scenarios."""

import pytest

from intellicare_core.subscriptions.matcher import FHIRCriteriaMatcher


# ── Resource fixtures ──────────────────────────────────────────────────────

OBS_GLUCOSE = {
    "resourceType": "Observation",
    "id": "obs-001",
    "status": "final",
    "code": {
        "coding": [{"system": "http://loinc.org", "code": "2345-7", "display": "glucose"}]
    },
    "subject": {"reference": "Patient/patient-123"},
    "valueQuantity": {"value": 250, "unit": "mg/dL"},
    "category": [
        {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}
    ],
}

OBS_HR = {
    "resourceType": "Observation",
    "id": "obs-002",
    "status": "final",
    "code": {
        "coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]
    },
    "subject": {"reference": "Patient/patient-123"},
    "valueQuantity": {"value": 80, "unit": "beats/minute"},
    "category": [
        {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}
    ],
}

PATIENT_SILVA = {
    "resourceType": "Patient",
    "id": "patient-123",
    "active": True,
    "gender": "male",
    "birthDate": "1980-01-01",
    "name": [{"family": "Silva", "given": ["João"]}],
}

CONDITION_DIABETES = {
    "resourceType": "Condition",
    "id": "cond-001",
    "clinicalStatus": {"coding": [{"code": "active"}]},
    "subject": {"reference": "Patient/patient-123"},
    "code": {"coding": [{"system": "http://snomed.info/sct", "code": "73211009", "display": "Diabetes mellitus"}]},
}


# ── parse_criteria ─────────────────────────────────────────────────────────

class TestParseCriteria:
    def test_resource_only(self):
        m = FHIRCriteriaMatcher("Observation")
        assert m.resource_type == "Observation"
        assert m.params == []

    def test_resource_with_params(self):
        m = FHIRCriteriaMatcher("Observation?status=final")
        assert m.resource_type == "Observation"
        assert len(m.params) == 1
        assert m.params[0].key == "status"
        assert m.params[0].comparator == "eq"
        assert m.params[0].value == "final"

    def test_multiple_params(self):
        m = FHIRCriteriaMatcher("Observation?status=final&subject=Patient/123")
        assert len(m.params) == 2

    def test_comparator_extraction_gt(self):
        m = FHIRCriteriaMatcher("Observation?value-quantity=gt200")
        assert m.params[0].comparator == "gt"
        assert m.params[0].value == "200"

    def test_comparator_extraction_le(self):
        m = FHIRCriteriaMatcher("Patient?birthdate=le2000-01-01")
        assert m.params[0].comparator == "le"
        assert m.params[0].value == "2000-01-01"

    def test_modifier_parsed(self):
        m = FHIRCriteriaMatcher("Patient?name:exact=Silva")
        assert m.params[0].modifier == "exact"
        assert m.params[0].key == "name"


# ── matches() ─────────────────────────────────────────────────────────────

class TestMatches:
    def test_resource_type_filter(self):
        m = FHIRCriteriaMatcher("Patient")
        assert m.matches(PATIENT_SILVA)
        assert not m.matches(OBS_GLUCOSE)

    def test_status_exact_match(self):
        m = FHIRCriteriaMatcher("Observation?status=final")
        assert m.matches(OBS_GLUCOSE)
        assert not m.matches({**OBS_GLUCOSE, "status": "preliminary"})

    def test_status_no_match(self):
        m = FHIRCriteriaMatcher("Observation?status=amended")
        assert not m.matches(OBS_GLUCOSE)

    def test_subject_reference_match(self):
        m = FHIRCriteriaMatcher("Observation?subject=Patient/patient-123")
        assert m.matches(OBS_GLUCOSE)

    def test_subject_reference_no_match(self):
        m = FHIRCriteriaMatcher("Observation?subject=Patient/other")
        assert not m.matches(OBS_GLUCOSE)

    def test_code_coding_match(self):
        m = FHIRCriteriaMatcher("Observation?code=glucose")
        assert m.matches(OBS_GLUCOSE)

    def test_category_match(self):
        m = FHIRCriteriaMatcher("Observation?category=vital-signs")
        assert m.matches(OBS_HR)
        assert not m.matches(OBS_GLUCOSE)

    def test_value_quantity_gt_match(self):
        m = FHIRCriteriaMatcher("Observation?value-quantity=gt200")
        assert m.matches(OBS_GLUCOSE)  # value=250 > 200

    def test_value_quantity_gt_no_match(self):
        m = FHIRCriteriaMatcher("Observation?value-quantity=gt300")
        assert not m.matches(OBS_GLUCOSE)  # value=250 < 300

    def test_value_quantity_lt_match(self):
        m = FHIRCriteriaMatcher("Observation?value-quantity=lt300")
        assert m.matches(OBS_GLUCOSE)

    def test_value_quantity_ge_boundary(self):
        m = FHIRCriteriaMatcher("Observation?value-quantity=ge250")
        assert m.matches(OBS_GLUCOSE)

    def test_value_quantity_le_boundary(self):
        m = FHIRCriteriaMatcher("Observation?value-quantity=le250")
        assert m.matches(OBS_GLUCOSE)

    def test_ne_comparator(self):
        m = FHIRCriteriaMatcher("Observation?status=ne")
        # "ne" comparator with value "ne" would try to match status != "ne"
        # status="final" != "ne" → True
        m2 = FHIRCriteriaMatcher("Observation?value-quantity=ne999")
        assert m2.matches(OBS_GLUCOSE)  # 250 != 999

    def test_multi_param_all_must_match(self):
        m = FHIRCriteriaMatcher("Observation?status=final&value-quantity=gt200")
        assert m.matches(OBS_GLUCOSE)

    def test_multi_param_one_fails(self):
        m = FHIRCriteriaMatcher("Observation?status=final&value-quantity=gt300")
        assert not m.matches(OBS_GLUCOSE)

    def test_patient_gender_match(self):
        m = FHIRCriteriaMatcher("Patient?gender=male")
        assert m.matches(PATIENT_SILVA)
        assert not m.matches({**PATIENT_SILVA, "gender": "female"})

    def test_patient_active_match(self):
        m = FHIRCriteriaMatcher("Patient?active=true")
        assert m.matches(PATIENT_SILVA)

    def test_patient_name_family_match(self):
        m = FHIRCriteriaMatcher("Patient?family=Silva")
        assert m.matches(PATIENT_SILVA)

    def test_resource_type_mismatch_fails(self):
        m = FHIRCriteriaMatcher("Condition?status=active")
        assert not m.matches(OBS_GLUCOSE)

    def test_empty_resource(self):
        m = FHIRCriteriaMatcher("Observation?status=final")
        assert not m.matches({"resourceType": "Observation"})
