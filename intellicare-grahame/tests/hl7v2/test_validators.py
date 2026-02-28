"""Tests for HL7v2 Validators."""

import pytest

from grahame.hl7v2.parser import HL7v2Parser
from grahame.hl7v2.validators import (
    FieldValidator,
    MessageValidator,
    StructureValidator,
    ValidationError,
)


@pytest.fixture
def valid_adt_a04_message() -> str:
    """Valid ADT^A04 message."""
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^^^HOSPITAL^MR||Silva^João^Carlos||19800101|M|||Rua Teste, 123^^São Paulo^SP^01234-567^BR||5511999999999\r"
        "PV1|1|I|2000^01^Hospital Central^^^^BR|||||||||||||||||||||||||||||||||||||20260224100000\r"
    )


@pytest.fixture
def message_missing_pid() -> str:
    """Message missing required PID segment."""
    return "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"


@pytest.fixture
def message_missing_patient_id() -> str:
    """Message with PID but missing patient ID (PID-3)."""
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||||Silva^João^Carlos||19800101|M\r"
    )


@pytest.fixture
def message_missing_patient_name() -> str:
    """Message with PID but missing patient name (PID-5)."""
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^^^HOSPITAL^MR||||19800101|M\r"
    )


def test_structure_validator_valid_message(valid_adt_a04_message):
    """Test structure validator with valid message."""
    parser = HL7v2Parser(valid_adt_a04_message)
    validator = StructureValidator()

    is_valid, error = validator.validate_required_segments(parser, "ADT^A04")

    assert is_valid is True
    assert error is None


def test_structure_validator_missing_pid(message_missing_pid):
    """Test structure validator detects missing PID segment."""
    parser = HL7v2Parser(message_missing_pid)
    validator = StructureValidator()

    is_valid, error = validator.validate_required_segments(parser, "ADT^A04")

    assert is_valid is False
    assert "PID" in error
    assert "missing" in error.lower()


def test_structure_validator_unsupported_message_type(valid_adt_a04_message):
    """Test structure validator with unsupported message type."""
    parser = HL7v2Parser(valid_adt_a04_message)
    validator = StructureValidator()

    is_valid, error = validator.validate_required_segments(parser, "ORU^R01")

    assert is_valid is False
    assert "Unsupported" in error


def test_field_validator_valid_message(valid_adt_a04_message):
    """Test field validator with valid message."""
    parser = HL7v2Parser(valid_adt_a04_message)
    validator = FieldValidator()

    is_valid, error = validator.validate_required_fields(parser, "ADT^A04")

    assert is_valid is True
    assert error is None


def test_field_validator_missing_patient_id(message_missing_patient_id):
    """Test field validator detects missing patient ID (PID-3)."""
    parser = HL7v2Parser(message_missing_patient_id)
    validator = FieldValidator()

    is_valid, error = validator.validate_required_fields(parser, "ADT^A04")

    assert is_valid is False
    assert "PID-3" in error
    assert "missing" in error.lower()


def test_field_validator_missing_patient_name(message_missing_patient_name):
    """Test field validator detects missing patient name (PID-5)."""
    parser = HL7v2Parser(message_missing_patient_name)
    validator = FieldValidator()

    is_valid, error = validator.validate_required_fields(parser, "ADT^A04")

    assert is_valid is False
    assert "PID-5" in error
    assert "missing" in error.lower()


def test_message_validator_valid_message(valid_adt_a04_message):
    """Test message validator with valid message."""
    parser = HL7v2Parser(valid_adt_a04_message)
    validator = MessageValidator()

    is_valid, error = validator.validate_adt_a04(parser)

    assert is_valid is True
    assert error is None


def test_message_validator_missing_segment(message_missing_pid):
    """Test message validator detects missing segment."""
    parser = HL7v2Parser(message_missing_pid)
    validator = MessageValidator()

    is_valid, error = validator.validate_adt_a04(parser)

    assert is_valid is False
    assert "PID" in error


def test_message_validator_missing_field(message_missing_patient_id):
    """Test message validator detects missing field."""
    parser = HL7v2Parser(message_missing_patient_id)
    validator = MessageValidator()

    is_valid, error = validator.validate_adt_a04(parser)

    assert is_valid is False
    assert "PID-3" in error


def test_message_validator_with_optional_pv1(valid_adt_a04_message):
    """Test message validator accepts message with optional PV1."""
    parser = HL7v2Parser(valid_adt_a04_message)
    validator = MessageValidator()

    is_valid, error = validator.validate_adt_a04(parser)

    assert is_valid is True
    assert error is None


def test_message_validator_without_pv1():
    """Test message validator accepts message without optional PV1."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^^^HOSPITAL^MR||Silva^João^Carlos||19800101|M\r"
    )
    parser = HL7v2Parser(message)
    validator = MessageValidator()

    is_valid, error = validator.validate_adt_a04(parser)

    assert is_valid is True
    assert error is None

