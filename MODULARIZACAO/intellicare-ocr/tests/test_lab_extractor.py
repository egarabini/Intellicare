from __future__ import annotations

from ocr.engine.lab_extractor import LabResultExtractor


def test_lab_extractor_maps_known_exams() -> None:
    text = """
    Creatinina: 2,1 mg/dL
    Potassio 5.6 mEq/L
    Ureia 82 mg/dL
    """
    lab_results, unrecognized, confidence = LabResultExtractor().extract(text)
    assert lab_results["creatinine"] == 2.1
    assert lab_results["potassium"] == 5.6
    assert lab_results["urea"] == 82.0
    assert confidence >= 0.6
    assert unrecognized == []


def test_lab_extractor_handles_missing_numeric_value() -> None:
    text = "Creatinina: resultado indisponivel"
    lab_results, unrecognized, confidence = LabResultExtractor().extract(text)
    assert lab_results == {}
    assert len(unrecognized) >= 1
    assert confidence < 0.6

