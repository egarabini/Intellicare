"""Tests for ADT^A04 Message Handler."""

import pytest

from grahame.hl7v2.messages.adt_a04 import ADTA04Handler, ADTMessage
from grahame.hl7v2.parser import HL7v2Parser


@pytest.fixture
def valid_adt_a04() -> str:
    """Valid ADT^A04 message."""
    pv1_fields = ["1", "I", "2000^01^Hospital Central^^^^BR"] + [""] * 40 + ["20260224100000"]
    pv1_segment = "PV1|" + "|".join(pv1_fields)
    
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^CPF^BR||Silva^João^Maria||19800101|M|||Rua Teste, 123^^São Paulo^SP^01234-567^BR||5511999999999\r"
        + pv1_segment
    )


@pytest.fixture
def invalid_message_type() -> str:
    """Message with wrong type (not ADT^A04)."""
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A01|MSG00002|P|2.5\r"
        "PID|1||12345678900^CPF^BR||Silva^João||19800101|M\r"
    )


@pytest.fixture
def missing_patient_id() -> str:
    """ADT^A04 message missing required PID-3 (Patient ID)."""
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00003|P|2.5\r"
        "PID|1||||Silva^João||19800101|M\r"
    )


@pytest.fixture
def missing_patient_name() -> str:
    """ADT^A04 message missing required PID-5 (Patient Name)."""
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00004|P|2.5\r"
        "PID|1||12345678900^CPF^BR||||19800101|M\r"
    )


# ── ADTMessage Tests ──────────────────────────────────────────────────────────


def test_adt_message_from_parser(valid_adt_a04):
    """Test ADTMessage parsing from valid message."""
    parser = HL7v2Parser(valid_adt_a04)
    adt_msg = ADTMessage.from_parser(parser)

    assert adt_msg.msh is not None
    assert adt_msg.msh.message_type == "ADT^A04"
    assert adt_msg.msh.message_control_id == "MSG00001"

    assert adt_msg.pid is not None
    assert len(adt_msg.pid.patient_id_list) == 1
    assert adt_msg.pid.patient_name["family"] == "Silva"

    assert adt_msg.pv1 is not None
    assert adt_msg.pv1.patient_class == "imp"


def test_adt_message_without_pv1():
    """Test ADTMessage parsing without PV1 segment."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00005|P|2.5\r"
        "PID|1||12345678900^CPF^BR||Silva^João||19800101|M\r"
    )
    parser = HL7v2Parser(message)
    adt_msg = ADTMessage.from_parser(parser)

    assert adt_msg.msh is not None
    assert adt_msg.pid is not None
    assert adt_msg.pv1 is None  # PV1 is optional


def test_adt_message_validate_success(valid_adt_a04):
    """Test ADTMessage validation with valid message."""
    parser = HL7v2Parser(valid_adt_a04)
    adt_msg = ADTMessage.from_parser(parser)

    is_valid, error = adt_msg.validate()
    assert is_valid is True
    assert error is None


def test_adt_message_validate_missing_patient_id(missing_patient_id):
    """Test ADTMessage validation fails when PID-3 is missing."""
    parser = HL7v2Parser(missing_patient_id)
    adt_msg = ADTMessage.from_parser(parser)

    is_valid, error = adt_msg.validate()
    assert is_valid is False
    assert "Patient ID List" in error


def test_adt_message_validate_missing_patient_name(missing_patient_name):
    """Test ADTMessage validation fails when PID-5 is missing."""
    parser = HL7v2Parser(missing_patient_name)
    adt_msg = ADTMessage.from_parser(parser)

    is_valid, error = adt_msg.validate()
    assert is_valid is False
    assert "Patient Name" in error


# ── ADTA04Handler Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handler_success(valid_adt_a04):
    """Test handler processes valid ADT^A04 message successfully."""
    handler = ADTA04Handler()
    ack, status_code = await handler.handle(valid_adt_a04)

    assert status_code == 200
    assert "MSA|AA|MSG00001" in ack  # AA = Application Accept
    assert "Message accepted" in ack


@pytest.mark.asyncio
async def test_handler_wrong_message_type(invalid_message_type):
    """Test handler rejects non-ADT^A04 messages."""
    handler = ADTA04Handler()
    ack, status_code = await handler.handle(invalid_message_type)

    assert status_code == 400
    assert "MSA|AR|MSG00002" in ack  # AR = Application Reject
    assert "Unsupported message type" in ack


@pytest.mark.asyncio
async def test_handler_validation_failure(missing_patient_id):
    """Test handler rejects message with validation errors."""
    handler = ADTA04Handler()
    ack, status_code = await handler.handle(missing_patient_id)

    assert status_code == 400
    assert "MSA|AR|MSG00003" in ack  # AR = Application Reject
    assert "Patient ID List" in ack


@pytest.mark.asyncio
async def test_handler_malformed_message():
    """Test handler handles malformed messages gracefully."""
    handler = ADTA04Handler()
    malformed = "INVALID HL7 MESSAGE"

    ack, status_code = await handler.handle(malformed)

    # Malformed message is treated as unsupported message type (400)
    assert status_code == 400
    assert "MSA|AR" in ack  # AR = Application Reject

