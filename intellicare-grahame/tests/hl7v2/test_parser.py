"""Tests for HL7v2 Parser Core."""

import pytest

from grahame.hl7v2.parser import HL7v2Parser
from grahame.hl7v2.segments import MSHSegment, PIDSegment, PV1Segment


@pytest.fixture
def sample_adt_a04() -> str:
    """Sample ADT^A04 message."""
    # PV1 has 44 fields, so we need to pad with empty fields to reach field 44
    pv1_fields = ["1", "I", "2000^01^Hospital Central^^^^BR"] + [""] * 40 + ["20260224100000"]
    pv1_segment = "PV1|" + "|".join(pv1_fields)

    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^^^HOSPITAL^CPF||Silva^João^Maria||19800101|M|||Rua Teste, 123^^São Paulo^SP^01234-567^BR||5511999999999\r"
        + pv1_segment
    )


def test_parse_msh(sample_adt_a04):
    """Test MSH segment parsing."""
    parser = HL7v2Parser(sample_adt_a04)

    assert parser.message_type == "ADT^A04"
    assert parser.message_control_id == "MSG00001"
    assert parser.timestamp == "20260224100000"


def test_parse_msh_segment(sample_adt_a04):
    """Test MSH segment model."""
    parser = HL7v2Parser(sample_adt_a04)
    msh = MSHSegment.from_parser(parser)

    assert msh.sending_application == "HOSPITAL"
    assert msh.sending_facility == "FACILITY"
    assert msh.receiving_application == "GRAHAME"
    assert msh.receiving_facility == "INTELLICARE"
    assert msh.message_type == "ADT^A04"
    assert msh.message_control_id == "MSG00001"
    assert msh.version == "2.5"
    assert msh.trigger_event == "A04"


def test_parse_pid(sample_adt_a04):
    """Test PID segment parsing."""
    parser = HL7v2Parser(sample_adt_a04)
    pid = PIDSegment.from_parser(parser)

    assert len(pid.patient_id_list) == 1
    assert pid.patient_id_list[0]["id"] == "12345678900"
    assert pid.patient_id_list[0]["assigning_authority"] == "HOSPITAL"
    assert pid.patient_id_list[0]["identifier_type"] == "CPF"
    
    assert pid.patient_name is not None
    assert pid.patient_name["family"] == "Silva"
    assert pid.patient_name["given"] == "João"
    assert pid.patient_name["middle"] == "Maria"
    
    assert pid.administrative_sex == "male"
    assert pid.datetime_of_birth == "1980-01-01"
    
    assert pid.address is not None
    assert pid.address["street"] == "Rua Teste, 123"
    assert pid.address["city"] == "São Paulo"
    assert pid.address["state"] == "SP"
    assert pid.address["postal_code"] == "01234-567"
    assert pid.address["country"] == "BR"
    
    assert pid.phone_number is not None
    assert pid.phone_number["number"] == "5511999999999"


def test_parse_pv1(sample_adt_a04):
    """Test PV1 segment parsing."""
    parser = HL7v2Parser(sample_adt_a04)
    pv1 = PV1Segment.from_parser(parser)

    assert pv1.set_id == "1"
    assert pv1.patient_class == "imp"  # I -> imp (inpatient)
    
    assert pv1.assigned_location is not None
    assert pv1.assigned_location["point_of_care"] == "2000"
    assert pv1.assigned_location["room"] == "01"
    assert pv1.assigned_location["bed"] == "Hospital Central"
    
    assert pv1.admit_datetime == "2026-02-24T10:00:00"


def test_parse_empty_message():
    """Test parsing empty message."""
    parser = HL7v2Parser("")
    
    assert parser.message_type is None
    assert parser.message_control_id is None
    assert parser.timestamp is None


def test_parse_missing_segment():
    """Test parsing message with missing segment."""
    message = "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
    parser = HL7v2Parser(message)
    
    pid = PIDSegment.from_parser(parser)
    
    # Should return empty/None values
    assert len(pid.patient_id_list) == 0
    assert pid.patient_name is None
    assert pid.datetime_of_birth is None


def test_ts_to_iso8601():
    """Test TS to ISO 8601 conversion."""
    # Full timestamp
    assert PIDSegment._ts_to_iso8601("20260224100000") == "2026-02-24T10:00:00"
    
    # Date only
    assert PIDSegment._ts_to_iso8601("20260224") == "2026-02-24"
    
    # Invalid
    assert PIDSegment._ts_to_iso8601("") is None
    assert PIDSegment._ts_to_iso8601("123") is None


def test_gender_mapping():
    """Test gender mapping."""
    assert PIDSegment._map_gender("M") == "male"
    assert PIDSegment._map_gender("F") == "female"
    assert PIDSegment._map_gender("U") == "unknown"
    assert PIDSegment._map_gender("O") == "other"
    assert PIDSegment._map_gender("X") == "unknown"  # Unknown code


def test_patient_class_mapping():
    """Test patient class mapping."""
    assert PV1Segment._map_patient_class("I") == "imp"  # Inpatient
    assert PV1Segment._map_patient_class("O") == "amb"  # Outpatient
    assert PV1Segment._map_patient_class("E") == "emer"  # Emergency
    assert PV1Segment._map_patient_class("P") == "imp"  # Preadmit
    assert PV1Segment._map_patient_class("X") == "amb"  # Unknown -> ambulatory


def test_parse_with_newline_separator():
    """Test parsing message with \\n instead of \\r."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\n"
        "PID|1||12345678900^^^HOSPITAL^CPF||Silva^João||19800101|M\n"
        "PV1|1|I|2000^01^Hospital Central"
    )
    parser = HL7v2Parser(message)
    
    assert parser.message_type == "ADT^A04"
    
    pid = PIDSegment.from_parser(parser)
    assert pid.patient_name["family"] == "Silva"

