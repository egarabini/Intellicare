from __future__ import annotations

from ocr.engine.discharge_extractor import DischargeExtractor


def test_discharge_extractor_extracts_cid_date_and_medication() -> None:
    text = (
        "Alta em 2026-02-10. Diagnostico principal N18.3. "
        "Metformina 500mg 2x ao dia."
    )
    payload = DischargeExtractor().extract(text)
    assert payload["discharge_date"] == "2026-02-10"
    assert payload["primary_diagnosis"]["cid10"] == "N18.3"
    assert len(payload["medications"]) == 1
    assert payload["confidence_score"] >= 0.6


def test_discharge_extractor_returns_low_confidence_without_structure() -> None:
    payload = DischargeExtractor().extract("texto sem padrao clinico")
    assert payload["primary_diagnosis"] is None
    assert payload["medications"] == []
    assert payload["confidence_score"] < 0.6

