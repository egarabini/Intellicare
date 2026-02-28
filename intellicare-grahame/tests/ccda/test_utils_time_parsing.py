from lxml import etree

from grahame.ccda.utils import (
    extract_effective_period_frequency,
    extract_effective_time_period,
    extract_effective_time_point,
    hl7_ts_to_iso8601,
)


NS = {"cda": "urn:hl7-org:v3"}


def _node(xml_fragment: str):
    return etree.fromstring(xml_fragment.encode("utf-8"))


def test_hl7_ts_to_iso8601_date_only():
    assert hl7_ts_to_iso8601("20260225") == "2026-02-25"


def test_hl7_ts_to_iso8601_datetime():
    assert hl7_ts_to_iso8601("20260225112233") == "2026-02-25T11:22:33"


def test_hl7_ts_to_iso8601_invalid():
    assert hl7_ts_to_iso8601("2026") is None


def test_extract_effective_time_point_from_value():
    node = _node('<observation xmlns="urn:hl7-org:v3"><effectiveTime value="20260225101010"/></observation>')
    assert extract_effective_time_point(node, NS) == "2026-02-25T10:10:10"


def test_extract_effective_time_point_from_low():
    node = _node('<observation xmlns="urn:hl7-org:v3"><effectiveTime><low value="20260225101010"/></effectiveTime></observation>')
    assert extract_effective_time_point(node, NS) == "2026-02-25T10:10:10"


def test_extract_effective_time_point_from_center():
    node = _node('<observation xmlns="urn:hl7-org:v3"><effectiveTime><center value="20260225101010"/></effectiveTime></observation>')
    assert extract_effective_time_point(node, NS) == "2026-02-25T10:10:10"


def test_extract_effective_time_point_from_high_fallback():
    node = _node('<observation xmlns="urn:hl7-org:v3"><effectiveTime><high value="20260225101010"/></effectiveTime></observation>')
    assert extract_effective_time_point(node, NS) == "2026-02-25T10:10:10"


def test_extract_effective_time_point_from_phase_low():
    node = _node('<observation xmlns="urn:hl7-org:v3"><effectiveTime><phase><low value="20260225101010"/></phase></effectiveTime></observation>')
    assert extract_effective_time_point(node, NS) == "2026-02-25T10:10:10"


def test_extract_effective_time_point_from_phase_center():
    node = _node('<observation xmlns="urn:hl7-org:v3"><effectiveTime><phase><center value="20260225101010"/></phase></effectiveTime></observation>')
    assert extract_effective_time_point(node, NS) == "2026-02-25T10:10:10"


def test_extract_effective_time_period_low_high():
    node = _node('<encounter xmlns="urn:hl7-org:v3"><effectiveTime><low value="20260225100000"/><high value="20260225110000"/></effectiveTime></encounter>')
    assert extract_effective_time_period(node, NS) == {"start": "2026-02-25T10:00:00", "end": "2026-02-25T11:00:00"}


def test_extract_effective_time_period_center_only():
    node = _node('<encounter xmlns="urn:hl7-org:v3"><effectiveTime><center value="20260225103000"/></effectiveTime></encounter>')
    assert extract_effective_time_period(node, NS) == {"start": "2026-02-25T10:30:00"}


def test_extract_effective_time_period_phase_interval():
    node = _node('<encounter xmlns="urn:hl7-org:v3"><effectiveTime><phase><low value="20260225100000"/><high value="20260225110000"/></phase></effectiveTime></encounter>')
    assert extract_effective_time_period(node, NS) == {"start": "2026-02-25T10:00:00", "end": "2026-02-25T11:00:00"}


def test_extract_effective_time_period_none_when_missing():
    node = _node('<encounter xmlns="urn:hl7-org:v3"><effectiveTime/></encounter>')
    assert extract_effective_time_period(node, NS) is None


def test_extract_effective_period_frequency_operator_a():
    node = _node('<substanceAdministration xmlns="urn:hl7-org:v3"><effectiveTime operator="A"><period value="12" unit="h"/></effectiveTime></substanceAdministration>')
    assert extract_effective_period_frequency(node, NS) == {"value": "12", "unit": "h"}


def test_extract_effective_period_frequency_direct_period():
    node = _node('<substanceAdministration xmlns="urn:hl7-org:v3"><effectiveTime><period value="1" unit="d"/></effectiveTime></substanceAdministration>')
    assert extract_effective_period_frequency(node, NS) == {"value": "1", "unit": "d"}


def test_extract_effective_period_frequency_phase_period():
    node = _node('<substanceAdministration xmlns="urn:hl7-org:v3"><effectiveTime><phase><period value="8" unit="h"/></phase></effectiveTime></substanceAdministration>')
    assert extract_effective_period_frequency(node, NS) == {"value": "8", "unit": "h"}


def test_extract_effective_period_frequency_none_when_missing():
    node = _node('<substanceAdministration xmlns="urn:hl7-org:v3"><effectiveTime/></substanceAdministration>')
    assert extract_effective_period_frequency(node, NS) is None
