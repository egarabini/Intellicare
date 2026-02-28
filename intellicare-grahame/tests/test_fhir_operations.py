"""Testes para as operações FHIR R4 (W1-A)."""

import pytest
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.fhir.compartment import (
    extract_references,
    get_patient_ref,
    resource_belongs_to_patient,
)
from grahame.fhir.ips_sections import classify_observation, classify_condition, classify_resource
from grahame.fhir.fhir_error import operation_outcome_from_errors
from grahame.fhir.operations.patient_everything import EverythingParams, patient_everything
from grahame.fhir.operations.patient_summary import patient_summary
from grahame.fhir.operations.resource_validate import validate_resource
from grahame.fhir.operations.measure_evaluate import evaluate_measure
from grahame.fhir.operations.valueset_expand import expand_valueset
from grahame.models.fhir_resource import FHIRResource
from grahame.models.codesystem_concept import CodeSystemConcept

from .conftest import PATIENT_SILVA, OBSERVATION_HEARTRATE


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de fixtures FHIR
# ─────────────────────────────────────────────────────────────────────────────

CONDITION_DIABETES = {
    "resourceType": "Condition",
    "id": "cond-001",
    "clinicalStatus": {"coding": [{"code": "active"}]},
    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "E11", "display": "Diabetes mellitus type 2"}]},
    "subject": {"reference": "Patient/patient-123"},
}

CONDITION_HEALTH_CONCERN = {
    "resourceType": "Condition",
    "id": "cond-002",
    "category": [{"coding": [{"code": "health-concern"}]}],
    "code": {"coding": [{"code": "Z13"}]},
    "subject": {"reference": "Patient/patient-123"},
}

OBSERVATION_SOCIAL = {
    "resourceType": "Observation",
    "id": "obs-social-001",
    "status": "final",
    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "social-history"}]}],
    "code": {"coding": [{"code": "72166-2", "display": "Tobacco smoking status"}]},
    "subject": {"reference": "Patient/patient-123"},
    "valueCodeableConcept": {"coding": [{"code": "266919005"}]},
}

MEDICATION_REQUEST = {
    "resourceType": "MedicationRequest",
    "id": "medr-001",
    "status": "active",
    "intent": "order",
    "medicationCodeableConcept": {"coding": [{"code": "metformin"}]},
    "subject": {"reference": "Patient/patient-123"},
}

MEASURE_DIABETES_CONTROL = {
    "resourceType": "Measure",
    "id": "measure-dm2-control",
    "status": "active",
    "scoring": {"coding": [{"code": "proportion"}]},
    "group": [{
        "id": "g1",
        "population": [
            {
                "code": {"coding": [{"code": "initial-population"}]},
                "criteria": {"language": "text/cql", "expression": "true"},
            },
            {
                "code": {"coding": [{"code": "denominator"}]},
                "criteria": {"language": "text/cql", "expression": "true"},
            },
            {
                "code": {"coding": [{"code": "numerator"}]},
                "criteria": {"language": "text/cql", "expression": "true"},
            },
        ],
    }],
}


async def _seed_resource(session: AsyncSession, resource: dict) -> FHIRResource:
    row = FHIRResource(
        resource_type=resource["resourceType"],
        fhir_id=resource["id"],
        resource=resource,
    )
    session.add(row)
    await session.flush()
    return row


# ─────────────────────────────────────────────────────────────────────────────
# Compartment helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestCompartment:
    def test_get_patient_ref_bare_id(self):
        assert get_patient_ref("123") == "Patient/123"

    def test_get_patient_ref_full(self):
        assert get_patient_ref("Patient/123") == "Patient/123"

    def test_resource_belongs_to_patient(self):
        obs = {"resourceType": "Observation", "id": "o1", "subject": {"reference": "Patient/123"}}
        assert resource_belongs_to_patient(obs, "Patient/123") is True

    def test_resource_not_belongs(self):
        obs = {"resourceType": "Observation", "id": "o1", "subject": {"reference": "Patient/456"}}
        assert resource_belongs_to_patient(obs, "Patient/123") is False

    def test_resource_patient_field(self):
        imm = {"resourceType": "Immunization", "id": "i1", "patient": {"reference": "Patient/123"}}
        assert resource_belongs_to_patient(imm, "Patient/123") is True

    def test_extract_references(self):
        resource = {
            "resourceType": "Observation",
            "subject": {"reference": "Patient/123"},
            "performer": [{"reference": "Practitioner/abc"}],
        }
        refs = extract_references(resource)
        assert "Patient/123" in refs
        assert "Practitioner/abc" in refs


# ─────────────────────────────────────────────────────────────────────────────
# IPS Sections
# ─────────────────────────────────────────────────────────────────────────────

class TestIPSSections:
    def test_classify_observation_vital_signs(self):
        obs = {
            "resourceType": "Observation",
            "category": [{"coding": [{"code": "vital-signs"}]}],
        }
        assert classify_observation(obs) == "vital_signs"

    def test_classify_observation_social_history(self):
        obs = {
            "resourceType": "Observation",
            "category": [{"coding": [{"code": "social-history"}]}],
        }
        assert classify_observation(obs) == "social_history"

    def test_classify_observation_default_results(self):
        obs = {"resourceType": "Observation", "category": []}
        assert classify_observation(obs) == "results"

    def test_classify_condition_problem_list(self):
        cond = {"resourceType": "Condition", "category": []}
        assert classify_condition(cond) == "problem_list"

    def test_classify_condition_health_concern(self):
        cond = {
            "resourceType": "Condition",
            "category": [{"coding": [{"code": "health-concern"}]}],
        }
        assert classify_condition(cond) == "health_concerns"

    def test_classify_resource_immunization(self):
        imm = {"resourceType": "Immunization"}
        assert classify_resource(imm) == "immunizations"

    def test_classify_resource_none_for_patient(self):
        patient = {"resourceType": "Patient"}
        assert classify_resource(patient) is None


# ─────────────────────────────────────────────────────────────────────────────
# $everything
# ─────────────────────────────────────────────────────────────────────────────

class TestPatientEverything:
    async def test_everything_not_found(self, session: AsyncSession):
        params = EverythingParams()
        with pytest.raises(Exception) as exc:
            await patient_everything("ghost-patient", params, session)
        assert "404" in str(exc.value.status_code)

    async def test_everything_patient_only(self, session: AsyncSession, patient_silva):
        params = EverythingParams()
        bundle = await patient_everything("patient-123", params, session)
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "searchset"
        assert bundle["total"] >= 1
        types_in_bundle = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Patient" in types_in_bundle

    async def test_everything_with_observation(self, session: AsyncSession, patient_silva, observation_heartrate):
        params = EverythingParams()
        bundle = await patient_everything("patient-123", params, session)
        types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Patient" in types
        assert "Observation" in types

    async def test_everything_with_condition(self, session: AsyncSession, patient_silva):
        await _seed_resource(session, CONDITION_DIABETES)
        await session.commit()

        params = EverythingParams()
        bundle = await patient_everything("patient-123", params, session)
        types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Condition" in types

    async def test_everything_type_filter(self, session: AsyncSession, patient_silva, observation_heartrate):
        await _seed_resource(session, CONDITION_DIABETES)
        await session.commit()

        params = EverythingParams(_type=["Observation"])
        bundle = await patient_everything("patient-123", params, session)
        types = set(e["resource"]["resourceType"] for e in bundle["entry"])
        # Deve incluir Patient e Observation, mas não Condition
        assert "Observation" in types
        assert "Condition" not in types

    async def test_everything_pagination(self, session: AsyncSession, patient_silva, observation_heartrate):
        params_full = EverythingParams(_count=1000)
        params_page = EverythingParams(_count=1, _offset=0)

        full = await patient_everything("patient-123", params_full, session)
        paged = await patient_everything("patient-123", params_page, session)

        assert full["total"] >= 2
        assert len(paged["entry"]) == 1
        assert paged["total"] == full["total"]

    async def test_everything_excludes_other_patient(self, session: AsyncSession, patient_silva):
        other_obs = {
            "resourceType": "Observation",
            "id": "obs-other",
            "status": "final",
            "code": {"coding": [{"code": "x"}]},
            "subject": {"reference": "Patient/patient-999"},
        }
        await _seed_resource(session, other_obs)
        await session.commit()

        params = EverythingParams()
        bundle = await patient_everything("patient-123", params, session)
        ids = [e["resource"].get("id") for e in bundle["entry"]]
        assert "obs-other" not in ids


# ─────────────────────────────────────────────────────────────────────────────
# $summary
# ─────────────────────────────────────────────────────────────────────────────

class TestPatientSummary:
    async def test_summary_not_found(self, session: AsyncSession):
        with pytest.raises(Exception) as exc:
            await patient_summary("ghost", session)
        assert "404" in str(exc.value.status_code)

    async def test_summary_bundle_type(self, session: AsyncSession, patient_silva):
        bundle = await patient_summary("patient-123", session)
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "document"

    async def test_summary_contains_composition(self, session: AsyncSession, patient_silva):
        bundle = await patient_summary("patient-123", session)
        types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Composition" in types
        assert "Patient" in types

    async def test_summary_vital_signs_section(self, session: AsyncSession, patient_silva, observation_heartrate):
        bundle = await patient_summary("patient-123", session)
        composition = next(
            e["resource"] for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Composition"
        )
        section_codes = [
            s.get("code", {}).get("coding", [{}])[0].get("code")
            for s in composition.get("section", [])
        ]
        # Observation vital-signs → seção 8716-3
        assert "8716-3" in section_codes

    async def test_summary_multiple_sections(self, session: AsyncSession, patient_silva):
        await _seed_resource(session, CONDITION_DIABETES)
        await _seed_resource(session, OBSERVATION_SOCIAL)
        await _seed_resource(session, MEDICATION_REQUEST)
        await session.commit()

        bundle = await patient_summary("patient-123", session)
        composition = next(
            e["resource"] for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Composition"
        )
        assert len(composition.get("section", [])) >= 3


# ─────────────────────────────────────────────────────────────────────────────
# $validate
# ─────────────────────────────────────────────────────────────────────────────

class TestResourceValidate:
    def test_valid_patient(self):
        outcome, is_valid = validate_resource("Patient", {"resourceType": "Patient", "id": "p1"})
        assert is_valid is True
        assert outcome["resourceType"] == "OperationOutcome"

    def test_invalid_missing_resource_type(self):
        outcome, is_valid = validate_resource("Patient", {"id": "p1"})
        assert is_valid is False
        assert any(i["severity"] == "error" for i in outcome["issue"])

    def test_wrong_resource_type(self):
        outcome, is_valid = validate_resource("Patient", {"resourceType": "Observation", "id": "o1"})
        assert is_valid is False

    def test_valid_observation(self):
        obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"coding": [{"code": "x"}]},
        }
        outcome, is_valid = validate_resource("Observation", obs)
        assert is_valid is True

    def test_invalid_status(self):
        obs = {
            "resourceType": "Observation",
            "status": "INVALID_STATUS",
            "code": {"coding": [{"code": "x"}]},
        }
        outcome, is_valid = validate_resource("Observation", obs)
        assert is_valid is False

    def test_update_mode_requires_id(self):
        patient = {"resourceType": "Patient"}
        outcome, is_valid = validate_resource("Patient", patient, mode="update")
        assert is_valid is False
        diagnostics = " ".join(i["diagnostics"] for i in outcome["issue"])
        assert "id" in diagnostics

    def test_update_mode_with_id_valid(self):
        patient = {"resourceType": "Patient", "id": "p-001"}
        outcome, is_valid = validate_resource("Patient", patient, mode="update")
        assert is_valid is True

    def test_operation_outcome_structure(self):
        errors = [
            {"severity": "error", "code": "required", "diagnostics": "field x missing", "location": ["x"]},
            {"severity": "warning", "code": "business-rule", "diagnostics": "recommended y"},
        ]
        outcome = operation_outcome_from_errors(errors)
        assert outcome["resourceType"] == "OperationOutcome"
        assert len(outcome["issue"]) == 2


# ─────────────────────────────────────────────────────────────────────────────
# $expand
# ─────────────────────────────────────────────────────────────────────────────

class TestValueSetExpand:
    async def test_expand_not_found(self, session: AsyncSession):
        with pytest.raises(Exception) as exc:
            await expand_valueset("non-existent-vs", session)
        assert "404" in str(exc.value.status_code)

    async def test_expand_valueset_with_concepts(self, session: AsyncSession):
        # Seed ValueSet
        vs = {
            "resourceType": "ValueSet",
            "id": "vs-loinc-vitals",
            "status": "active",
            "url": "http://loinc.org/vs/vitals",
            "compose": {"include": [{"system": "http://loinc.org"}]},
        }
        await _seed_resource(session, vs)

        # Seed CodeSystem concepts
        for code, display in [("8867-4", "Heart rate"), ("8310-5", "Body temperature"), ("85354-9", "Blood pressure")]:
            concept = CodeSystemConcept(
                codesystem_url="http://loinc.org",
                code=code,
                display=display,
                tenant_id="public",
            )
            session.add(concept)
        await session.commit()

        result = await expand_valueset("vs-loinc-vitals", session)
        assert result["resourceType"] == "ValueSet"
        assert result["expansion"]["total"] == 3
        codes = [c["code"] for c in result["expansion"]["contains"]]
        assert "8867-4" in codes

    async def test_expand_filter_text(self, session: AsyncSession):
        vs = {
            "resourceType": "ValueSet",
            "id": "vs-filter-test",
            "status": "active",
            "compose": {"include": [{"system": "http://loinc.org"}]},
        }
        await _seed_resource(session, vs)

        for code, display in [("8867-4", "Heart rate"), ("8310-5", "Body temperature")]:
            session.add(CodeSystemConcept(codesystem_url="http://loinc.org", code=code, display=display, tenant_id="public"))
        await session.commit()

        result = await expand_valueset("vs-filter-test", session, filter_text="heart")
        assert result["expansion"]["total"] == 1
        assert result["expansion"]["contains"][0]["code"] == "8867-4"

    async def test_expand_pagination(self, session: AsyncSession):
        vs = {
            "resourceType": "ValueSet",
            "id": "vs-paged",
            "status": "active",
            "compose": {"include": [{"system": "http://loinc.org/paged"}]},
        }
        await _seed_resource(session, vs)

        for i in range(10):
            session.add(CodeSystemConcept(
                codesystem_url="http://loinc.org/paged",
                code=f"code-{i:02d}",
                display=f"Display {i}",
                tenant_id="public",
            ))
        await session.commit()

        page1 = await expand_valueset("vs-paged", session, count=3, offset=0)
        page2 = await expand_valueset("vs-paged", session, count=3, offset=3)

        assert len(page1["expansion"]["contains"]) == 3
        assert len(page2["expansion"]["contains"]) == 3
        codes1 = {c["code"] for c in page1["expansion"]["contains"]}
        codes2 = {c["code"] for c in page2["expansion"]["contains"]}
        assert codes1.isdisjoint(codes2)


# ─────────────────────────────────────────────────────────────────────────────
# $evaluate-measure
# ─────────────────────────────────────────────────────────────────────────────

class TestMeasureEvaluate:
    async def test_evaluate_not_found(self, session: AsyncSession):
        with pytest.raises(Exception) as exc:
            await evaluate_measure("ghost-measure", date(2026, 1, 1), date(2026, 12, 31), session)
        assert "404" in str(exc.value.status_code)

    async def test_evaluate_returns_measure_report(self, session: AsyncSession, patient_silva):
        await _seed_resource(session, MEASURE_DIABETES_CONTROL)
        await session.commit()

        report = await evaluate_measure(
            "measure-dm2-control",
            date(2026, 1, 1),
            date(2026, 12, 31),
            session,
        )
        assert report["resourceType"] == "MeasureReport"
        assert report["status"] == "complete"
        assert report["measure"] == "Measure/measure-dm2-control"

    async def test_evaluate_has_groups(self, session: AsyncSession, patient_silva):
        await _seed_resource(session, MEASURE_DIABETES_CONTROL)
        await session.commit()

        report = await evaluate_measure(
            "measure-dm2-control",
            date(2026, 1, 1),
            date(2026, 12, 31),
            session,
        )
        assert len(report["group"]) >= 1
        group = report["group"][0]
        assert "population" in group

    async def test_evaluate_period_in_report(self, session: AsyncSession, patient_silva):
        await _seed_resource(session, MEASURE_DIABETES_CONTROL)
        await session.commit()

        report = await evaluate_measure(
            "measure-dm2-control",
            date(2026, 3, 1),
            date(2026, 6, 30),
            session,
        )
        assert report["period"]["start"] == "2026-03-01"
        assert report["period"]["end"] == "2026-06-30"

    async def test_evaluate_with_specific_subject(self, session: AsyncSession, patient_silva):
        await _seed_resource(session, MEASURE_DIABETES_CONTROL)
        await session.commit()

        report = await evaluate_measure(
            "measure-dm2-control",
            date(2026, 1, 1),
            date(2026, 12, 31),
            session,
            subject="Patient/patient-123",
        )
        assert report["subject"]["reference"] == "Patient/patient-123"
