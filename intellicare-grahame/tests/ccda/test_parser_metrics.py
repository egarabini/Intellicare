from pathlib import Path

import pytest

import grahame.ccda.parser as parser_mod
from grahame.ccda.parser import CCDAParser


FIXTURE = Path(__file__).parent / "fixtures" / "pv_ccda.xml"


def test_parser_exposes_section_metrics_and_errors():
    parser = CCDAParser()
    doc = parser.parse(FIXTURE.read_text(encoding="utf-8"))

    assert doc.patient is not None
    assert "patient" in parser.section_metrics
    assert "observations" in parser.section_metrics
    assert parser.section_metrics["patient"]["parsed"] == 1
    assert parser.section_metrics["patient"]["errors"] == 0
    assert isinstance(parser.errors, list)


def test_parser_records_section_error_and_continues(monkeypatch: pytest.MonkeyPatch):
    class _BoomResults:
        def __init__(self, _ns):
            pass

        def parse(self, _root):
            raise RuntimeError("synthetic results parsing failure")

    monkeypatch.setattr(parser_mod, "ResultsSectionParser", _BoomResults)

    parser = CCDAParser()
    doc = parser.parse(FIXTURE.read_text(encoding="utf-8"))

    assert doc.patient is not None
    assert doc.observations == []
    assert parser.section_metrics["observations"]["errors"] == 1
    assert any(e["section"] == "observations" for e in parser.errors)
