"""Testes para CorrelationDetector."""

from florence.engine.correlations.detector import CorrelationDetector
from florence.engine.models import ClinicalSignificance


class TestCorrelationDetector:
    def test_load_all(self, corr_detector: CorrelationDetector) -> None:
        assert len(corr_detector) >= 7

    def test_list_patterns(self, corr_detector: CorrelationDetector) -> None:
        patterns = corr_detector.list_patterns()
        assert "renal_impairment" in patterns
        assert "hepatic_injury" in patterns
        assert "metabolic_syndrome" in patterns
        assert "hyperkalemia_risk" in patterns

    def test_detect_renal_impairment(self, corr_detector: CorrelationDetector) -> None:
        results = {"creatinine": 2.5, "urea": 80.0}
        findings = corr_detector.detect(results)
        assert len(findings) >= 1
        renal = [f for f in findings if f.pattern_id == "renal_impairment"]
        assert len(renal) == 1
        assert renal[0].significance == ClinicalSignificance.URGENT
        assert len(renal[0].recommendations) >= 2

    def test_no_renal_impairment_normal(self, corr_detector: CorrelationDetector) -> None:
        results = {"creatinine": 0.9, "urea": 25.0}
        findings = corr_detector.detect(results)
        renal = [f for f in findings if f.pattern_id == "renal_impairment"]
        assert len(renal) == 0

    def test_detect_hepatic_injury(self, corr_detector: CorrelationDetector) -> None:
        results = {"ast": 500.0, "alt": 600.0}
        findings = corr_detector.detect(results)
        hepatic = [f for f in findings if f.pattern_id == "hepatic_injury"]
        assert len(hepatic) == 1
        assert hepatic[0].significance == ClinicalSignificance.URGENT

    def test_detect_metabolic_syndrome(self, corr_detector: CorrelationDetector) -> None:
        results = {"glucose_fasting": 120.0, "triglycerides": 250.0}
        findings = corr_detector.detect(results)
        metabolic = [f for f in findings if f.pattern_id == "metabolic_syndrome"]
        assert len(metabolic) == 1
        assert metabolic[0].significance == ClinicalSignificance.ATTENTION

    def test_detect_hyperkalemia_risk(self, corr_detector: CorrelationDetector) -> None:
        results = {"potassium": 6.0, "creatinine": 3.0}
        findings = corr_detector.detect(results)
        hyper = [f for f in findings if f.pattern_id == "hyperkalemia_risk"]
        assert len(hyper) == 1
        assert hyper[0].significance == ClinicalSignificance.CRITICAL

    def test_detect_anemia(self, corr_detector: CorrelationDetector) -> None:
        results = {"hemoglobin": 8.0}
        findings = corr_detector.detect(results)
        anemia = [f for f in findings if f.pattern_id == "anemia_investigation"]
        assert len(anemia) == 1

    def test_detect_thyroid_hypo(self, corr_detector: CorrelationDetector) -> None:
        results = {"tsh": 25.0}
        findings = corr_detector.detect(results)
        thyroid = [f for f in findings if f.pattern_id == "thyroid_dysfunction"]
        assert len(thyroid) == 1
        assert "hipotireoidismo" in thyroid[0].message

    def test_detect_thyroid_hyper(self, corr_detector: CorrelationDetector) -> None:
        results = {"tsh": 0.05}
        findings = corr_detector.detect(results)
        thyroid = [f for f in findings if f.pattern_id == "thyroid_dysfunction"]
        assert len(thyroid) == 1
        assert "hipertireoidismo" in thyroid[0].message

    def test_detect_coagulation_risk(self, corr_detector: CorrelationDetector) -> None:
        results = {"inr": 5.5}
        findings = corr_detector.detect(results)
        coag = [f for f in findings if f.pattern_id == "coagulation_risk"]
        assert len(coag) == 1
        assert coag[0].significance == ClinicalSignificance.CRITICAL

    def test_multiple_patterns(self, corr_detector: CorrelationDetector) -> None:
        results = {
            "creatinine": 3.0,
            "urea": 100.0,
            "potassium": 6.2,
            "hemoglobin": 8.5,
        }
        findings = corr_detector.detect(results)
        pattern_ids = [f.pattern_id for f in findings]
        assert "renal_impairment" in pattern_ids
        assert "hyperkalemia_risk" in pattern_ids
        assert "anemia_investigation" in pattern_ids

    def test_no_findings_normal(self, corr_detector: CorrelationDetector) -> None:
        results = {
            "creatinine": 0.9,
            "urea": 25.0,
            "potassium": 4.0,
            "hemoglobin": 14.0,
            "glucose_fasting": 85.0,
        }
        findings = corr_detector.detect(results)
        assert len(findings) == 0

    def test_missing_required_labs(self, corr_detector: CorrelationDetector) -> None:
        results = {"creatinine": 5.0}  # urea missing for renal_impairment
        findings = corr_detector.detect(results)
        renal = [f for f in findings if f.pattern_id == "renal_impairment"]
        assert len(renal) == 0

    def test_finding_to_dict(self, corr_detector: CorrelationDetector) -> None:
        results = {"creatinine": 2.5, "urea": 80.0}
        findings = corr_detector.detect(results)
        assert len(findings) >= 1
        d = findings[0].to_dict()
        assert "pattern_id" in d
        assert "message" in d
        assert "recommendations" in d
