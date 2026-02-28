"""Testes para LabInterpreter."""

from datetime import datetime, timezone

from florence.engine.lab_interpreter import LabInterpreter
from florence.engine.models import (
    ClinicalSignificance,
    InterpretationLevel,
)
from florence.engine.reference_ranges.loader import ReferenceRangeLoader


class TestLabInterpreter:
    def _make_interpreter(self, ref_loader: ReferenceRangeLoader) -> LabInterpreter:
        return LabInterpreter(ref_loader)

    def test_normal_creatinine(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("creatinine", 1.0)
        assert result is not None
        assert result.level == InterpretationLevel.NORMAL
        assert result.significance == ClinicalSignificance.ROUTINE
        assert "normalidade" in result.message

    def test_high_creatinine(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("creatinine", 2.5)
        assert result is not None
        assert result.level == InterpretationLevel.HIGH
        assert result.significance == ClinicalSignificance.ATTENTION

    def test_critical_high_creatinine(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("creatinine", 12.0)
        assert result is not None
        assert result.level == InterpretationLevel.CRITICAL_HIGH
        assert result.significance == ClinicalSignificance.URGENT

    def test_low_hemoglobin(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("hemoglobin", 11.0)
        assert result is not None
        assert result.level == InterpretationLevel.LOW

    def test_critical_low_hemoglobin(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("hemoglobin", 6.0)
        assert result is not None
        assert result.level == InterpretationLevel.CRITICAL_LOW
        assert result.significance == ClinicalSignificance.URGENT

    def test_panic_low_hemoglobin(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("hemoglobin", 4.5)
        assert result is not None
        assert result.level == InterpretationLevel.PANIC
        assert result.significance == ClinicalSignificance.CRITICAL
        assert "panico" in result.message

    def test_panic_high_potassium(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("potassium", 7.5)
        assert result is not None
        assert result.level == InterpretationLevel.PANIC

    def test_normal_glucose(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("glucose_fasting", 85.0)
        assert result is not None
        assert result.level == InterpretationLevel.NORMAL

    def test_high_glucose(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("glucose_fasting", 200.0)
        assert result is not None
        assert result.level == InterpretationLevel.HIGH

    def test_critical_high_glucose(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("glucose_fasting", 450.0)
        assert result is not None
        assert result.level == InterpretationLevel.CRITICAL_HIGH

    def test_panic_low_glucose(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("glucose_fasting", 25.0)
        assert result is not None
        assert result.level == InterpretationLevel.PANIC

    def test_nonexistent_lab(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("nonexistent", 42.0)
        assert result is None

    def test_interpret_by_loinc(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret_by_loinc("2160-0", 1.0)  # creatinine
        assert result is not None
        assert result.lab_id == "creatinine"

    def test_interpret_by_loinc_nonexistent(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret_by_loinc("99999-9", 1.0)
        assert result is None

    def test_interpret_batch(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        results = interp.interpret_batch({
            "creatinine": 1.0,
            "hemoglobin": 14.0,
            "glucose_fasting": 85.0,
        })
        assert len(results) == 3
        assert all(r.level == InterpretationLevel.NORMAL for r in results)

    def test_interpret_batch_with_abnormal(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        results = interp.interpret_batch({
            "creatinine": 5.0,
            "potassium": 6.0,
            "hemoglobin": 14.0,
        })
        abnormal = [r for r in results if r.level != InterpretationLevel.NORMAL]
        assert len(abnormal) == 2

    def test_interpret_with_timestamp(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        ts = datetime(2024, 6, 15, tzinfo=timezone.utc)
        result = interp.interpret("creatinine", 1.0, ts)
        assert result is not None
        assert result.timestamp == ts

    def test_to_dict(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("creatinine", 2.0)
        d = result.to_dict()
        assert d["lab_id"] == "creatinine"
        assert d["value"] == 2.0
        assert d["level"] == "high"
        assert "reference_range" in d

    def test_tsh_high(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("tsh", 15.0)
        assert result is not None
        assert result.level == InterpretationLevel.HIGH

    def test_tsh_critical_high(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("tsh", 55.0)
        assert result is not None
        assert result.level == InterpretationLevel.CRITICAL_HIGH

    def test_inr_normal(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("inr", 1.0)
        assert result is not None
        assert result.level == InterpretationLevel.NORMAL

    def test_inr_critical(self, ref_loader: ReferenceRangeLoader) -> None:
        interp = self._make_interpreter(ref_loader)
        result = interp.interpret("inr", 6.0)
        assert result is not None
        assert result.level == InterpretationLevel.CRITICAL_HIGH
