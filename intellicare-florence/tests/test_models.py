"""Testes para modelos de dados do Florence."""

from datetime import datetime, timezone

from florence.engine.models import (
    ClinicalAnalysis,
    ClinicalSignificance,
    CorrelationFinding,
    InterpretationLevel,
    LabInterpretation,
    TrendAnalysis,
    TrendDirection,
)


class TestLabInterpretation:
    def test_to_dict(self) -> None:
        interp = LabInterpretation(
            lab_id="creatinine",
            lab_name="Creatinina",
            loinc_code="2160-0",
            value=2.5,
            unit="mg/dL",
            level=InterpretationLevel.HIGH,
            reference_range="0.7-1.3 mg/dL",
            message="Creatinina acima do normal",
            significance=ClinicalSignificance.ATTENTION,
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        d = interp.to_dict()
        assert d["lab_id"] == "creatinine"
        assert d["level"] == "high"
        assert d["significance"] == "attention"
        assert "2024-01-15" in d["timestamp"]


class TestTrendAnalysis:
    def test_to_dict(self) -> None:
        trend = TrendAnalysis(
            lab_id="creatinine",
            lab_name="Creatinina",
            direction=TrendDirection.WORSENING,
            slope=0.02,
            current_value=2.5,
            previous_value=2.0,
            change_percent=25.0,
            period_days=90,
            data_points=5,
            message="Creatinina em alta",
        )
        d = trend.to_dict()
        assert d["direction"] == "worsening"
        assert d["slope"] == 0.02
        assert d["data_points"] == 5


class TestCorrelationFinding:
    def test_to_dict(self) -> None:
        finding = CorrelationFinding(
            pattern_id="renal_impairment",
            pattern_name="Comprometimento Renal",
            description="Padrao sugestivo de insuficiencia renal",
            labs_involved=["creatinine", "urea"],
            significance=ClinicalSignificance.URGENT,
            message="Elevacao conjunta",
            recommendations=["Solicitar eGFR"],
        )
        d = finding.to_dict()
        assert d["pattern_id"] == "renal_impairment"
        assert d["significance"] == "urgent"
        assert len(d["recommendations"]) == 1


class TestClinicalAnalysis:
    def test_to_dict(self) -> None:
        analysis = ClinicalAnalysis(
            patient_id="p-1",
            interpretations=[],
            trends=[],
            correlations=[],
            summary="Analise normal",
            significance=ClinicalSignificance.ROUTINE,
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        d = analysis.to_dict()
        assert d["patient_id"] == "p-1"
        assert d["significance"] == "routine"
        assert d["interpretations"] == []


class TestEnums:
    def test_interpretation_levels(self) -> None:
        assert InterpretationLevel.NORMAL.value == "normal"
        assert InterpretationLevel.PANIC.value == "panic"
        assert InterpretationLevel.CRITICAL_LOW.value == "critical_low"

    def test_clinical_significance(self) -> None:
        assert ClinicalSignificance.ROUTINE.value == "routine"
        assert ClinicalSignificance.CRITICAL.value == "critical"

    def test_trend_direction(self) -> None:
        assert TrendDirection.IMPROVING.value == "improving"
        assert TrendDirection.WORSENING.value == "worsening"
