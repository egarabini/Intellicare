"""Testes para ClinicalAnalyzer."""

from datetime import datetime, timedelta, timezone

from florence.engine.clinical_analyzer import ClinicalAnalyzer
from florence.engine.models import ClinicalSignificance, InterpretationLevel, TrendDirection


class TestClinicalAnalyzer:
    def test_analyze_all_normal(self, analyzer: ClinicalAnalyzer) -> None:
        result = analyzer.analyze_labs(
            "p-1",
            {"creatinine": 1.0, "hemoglobin": 14.0, "glucose_fasting": 85.0},
        )
        assert result.patient_id == "p-1"
        assert result.significance == ClinicalSignificance.ROUTINE
        assert len(result.interpretations) == 3
        assert len(result.correlations) == 0
        assert "normalidade" in result.summary

    def test_analyze_with_abnormal(self, analyzer: ClinicalAnalyzer) -> None:
        result = analyzer.analyze_labs(
            "p-1",
            {"creatinine": 5.0, "urea": 120.0, "potassium": 6.0},
        )
        assert result.significance in (ClinicalSignificance.URGENT, ClinicalSignificance.CRITICAL)
        assert len(result.correlations) >= 1  # renal_impairment at minimum

    def test_analyze_to_dict(self, analyzer: ClinicalAnalyzer) -> None:
        result = analyzer.analyze_labs("p-1", {"creatinine": 1.0})
        d = result.to_dict()
        assert d["patient_id"] == "p-1"
        assert "interpretations" in d
        assert "correlations" in d
        assert "summary" in d
        assert "significance" in d

    def test_analyze_with_trends(self, analyzer: ClinicalAnalyzer) -> None:
        now = datetime.now(timezone.utc)
        historical = {
            "creatinine": [
                (now - timedelta(days=90), 1.0),
                (now - timedelta(days=60), 1.5),
                (now - timedelta(days=30), 2.0),
                (now, 2.5),
            ]
        }
        result = analyzer.analyze_with_trends(
            "p-1",
            {"creatinine": 2.5, "urea": 60.0},
            historical,
        )
        assert len(result.trends) == 1
        assert result.trends[0].lab_id == "creatinine"
        assert result.trends[0].direction in (TrendDirection.WORSENING, TrendDirection.IMPROVING)

    def test_interpret_single(self, analyzer: ClinicalAnalyzer) -> None:
        result = analyzer.interpret_single("creatinine", 1.0)
        assert result is not None
        assert result.level == InterpretationLevel.NORMAL

    def test_interpret_single_nonexistent(self, analyzer: ClinicalAnalyzer) -> None:
        result = analyzer.interpret_single("nonexistent", 1.0)
        assert result is None

    def test_summary_format_abnormal(self, analyzer: ClinicalAnalyzer) -> None:
        result = analyzer.analyze_labs("p-1", {"creatinine": 5.0, "potassium": 6.5})
        assert "fora da referencia" in result.summary
        assert "Significancia clinica geral" in result.summary

    def test_summary_with_correlation(self, analyzer: ClinicalAnalyzer) -> None:
        result = analyzer.analyze_labs("p-1", {"creatinine": 3.0, "urea": 100.0})
        assert "padrao" in result.summary.lower()

    def test_empty_results(self, analyzer: ClinicalAnalyzer) -> None:
        result = analyzer.analyze_labs("p-1", {})
        assert result.significance == ClinicalSignificance.ROUTINE
        assert len(result.interpretations) == 0

    def test_clinical_significance_escalation(self, analyzer: ClinicalAnalyzer) -> None:
        # Potassium panic + creatinine high = highest significance wins
        result = analyzer.analyze_labs(
            "p-1",
            {"potassium": 7.5, "creatinine": 3.0},
        )
        assert result.significance == ClinicalSignificance.CRITICAL
