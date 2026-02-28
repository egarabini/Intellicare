from pathlib import Path

import pytest

from grahame.ccda.models import CCDADocument
from grahame.ccda.parser import CCDAParser


FIXTURE = Path(__file__).parent / "fixtures" / "sample_ccda.xml"


def test_parse_ccda_sample():
    parser = CCDAParser()
    doc = parser.parse(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(doc, CCDADocument)
    assert doc.patient.name["family"] == "Silva"
    assert doc.patient.birth_date == "1980-01-01"
    assert len(doc.observations) == 1
    assert doc.observations[0].code["code"] == "8867-4"
    assert parser.processing_time_ms > 0


def test_parse_invalid_xml():
    parser = CCDAParser()
    with pytest.raises(ValueError, match="Invalid XML"):
        parser.parse("not xml")
