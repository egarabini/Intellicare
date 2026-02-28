"""Testes para os modelos FHIR simplificados."""

from datetime import date, datetime, timezone

from intellicare_core.fhir.models import (
    AllergySummary,
    ConditionSummary,
    MedicationSummary,
    ObservationValue,
    PatientSummary,
)


class TestObservationValue:
    def test_normal_range(self) -> None:
        obs = ObservationValue(
            code="2160-0",
            value=1.0,
            reference_low=0.7,
            reference_high=1.2,
        )
        assert obs.is_abnormal is False

    def test_above_range(self) -> None:
        obs = ObservationValue(
            code="2160-0",
            value=1.5,
            reference_low=0.7,
            reference_high=1.2,
        )
        assert obs.is_abnormal is True

    def test_below_range(self) -> None:
        obs = ObservationValue(
            code="2160-0",
            value=0.3,
            reference_low=0.7,
            reference_high=1.2,
        )
        assert obs.is_abnormal is True

    def test_no_reference_not_abnormal(self) -> None:
        obs = ObservationValue(code="2160-0", value=999.0)
        assert obs.is_abnormal is False

    def test_no_value_not_abnormal(self) -> None:
        obs = ObservationValue(code="2160-0", reference_low=0.7, reference_high=1.2)
        assert obs.is_abnormal is False


class TestConditionSummary:
    def test_defaults(self) -> None:
        c = ConditionSummary(code="N18.3")
        assert c.clinical_status == "active"
        assert c.display == ""
        assert c.category == ""


class TestAllergySummary:
    def test_defaults(self) -> None:
        a = AllergySummary()
        assert a.substance == ""
        assert a.clinical_status == "active"


class TestMedicationSummary:
    def test_defaults(self) -> None:
        m = MedicationSummary()
        assert m.status == "active"
        assert m.name == ""


class TestPatientSummary:
    def test_age_calculation(self) -> None:
        summary = PatientSummary(
            patient_id="p-1",
            birth_date=date(1985, 3, 15),
        )
        assert summary.age is not None
        assert summary.age >= 40

    def test_age_none_without_birthdate(self) -> None:
        summary = PatientSummary(patient_id="p-1")
        assert summary.age is None

    def test_active_conditions(self) -> None:
        summary = PatientSummary(
            patient_id="p-1",
            conditions=[
                ConditionSummary(code="N18.3", clinical_status="active"),
                ConditionSummary(code="E11", clinical_status="resolved"),
                ConditionSummary(code="I10", clinical_status="active"),
            ],
        )
        assert len(summary.active_conditions) == 2

    def test_active_medications(self) -> None:
        summary = PatientSummary(
            patient_id="p-1",
            medications=[
                MedicationSummary(name="Enalapril", status="active"),
                MedicationSummary(name="Metformina", status="stopped"),
            ],
        )
        assert len(summary.active_medications) == 1
        assert summary.active_medications[0].name == "Enalapril"

    def test_get_latest_observation(self) -> None:
        summary = PatientSummary(
            patient_id="p-1",
            observations=[
                ObservationValue(
                    code="2160-0",
                    value=1.2,
                    date=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
                ObservationValue(
                    code="2160-0",
                    value=1.5,
                    date=datetime(2026, 1, 15, tzinfo=timezone.utc),
                ),
                ObservationValue(
                    code="33914-3",
                    value=52.3,
                    date=datetime(2026, 1, 15, tzinfo=timezone.utc),
                ),
            ],
        )
        latest = summary.get_latest_observation("2160-0")
        assert latest is not None
        assert latest.value == 1.5

    def test_get_latest_observation_not_found(self) -> None:
        summary = PatientSummary(patient_id="p-1")
        assert summary.get_latest_observation("2160-0") is None
