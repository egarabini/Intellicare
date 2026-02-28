"""Tests for ACK Generator."""

import pytest

from grahame.hl7v2.ack import ACKGenerator, build_simple_ack
from grahame.hl7v2.parser import HL7v2Parser
from grahame.hl7v2.segments import MSHSegment


@pytest.fixture
def sample_msh() -> MSHSegment:
    """Sample MSH segment."""
    message = "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
    parser = HL7v2Parser(message)
    return MSHSegment.from_parser(parser)


def test_generate_success_ack(sample_msh):
    """Test generating success ACK (AA)."""
    generator = ACKGenerator()
    ack = generator.generate_success(sample_msh)

    # Verify ACK structure
    assert "MSH|^~\\&" in ack
    assert "MSA|AA|MSG00001" in ack
    assert "Message accepted" in ack

    # Verify sender/receiver swap
    assert "|GRAHAME|INTELLICARE|HOSPITAL|FACILITY|" in ack

    # Verify message type
    assert "ACK^A04" in ack


def test_generate_reject_ack(sample_msh):
    """Test generating reject ACK (AR)."""
    generator = ACKGenerator()
    error_msg = "Invalid patient ID"
    ack = generator.generate_reject(sample_msh, error_msg)

    # Verify ACK structure
    assert "MSH|^~\\&" in ack
    assert "MSA|AR|MSG00001" in ack
    assert error_msg in ack


def test_generate_error_ack(sample_msh):
    """Test generating error ACK (AE)."""
    generator = ACKGenerator()
    error_msg = "Internal server error"
    ack = generator.generate_error(sample_msh, error_msg)

    # Verify ACK structure
    assert "MSH|^~\\&" in ack
    assert "MSA|AE|MSG00001" in ack
    assert error_msg in ack


def test_ack_has_unique_control_id(sample_msh):
    """Test that each ACK has a unique message control ID."""
    generator = ACKGenerator()
    ack1 = generator.generate_success(sample_msh)
    ack2 = generator.generate_success(sample_msh)

    # Extract MSH-10 (message control ID) from both ACKs
    # Format: MSH|...|...|...|...|...|...|...|...|CONTROL_ID|...
    ack1_parts = ack1.split("\r")[0].split("|")
    ack2_parts = ack2.split("\r")[0].split("|")

    ack1_ctrl_id = ack1_parts[9]  # MSH-10
    ack2_ctrl_id = ack2_parts[9]

    # Control IDs should be different (timestamp-based)
    assert ack1_ctrl_id != ack2_ctrl_id
    assert ack1_ctrl_id.startswith("ACK-")
    assert ack2_ctrl_id.startswith("ACK-")


def test_ack_preserves_version(sample_msh):
    """Test that ACK preserves HL7 version from original message."""
    generator = ACKGenerator()
    ack = generator.generate_success(sample_msh)

    # Verify version is preserved (MSH-12)
    assert "|2.5" in ack or "|2.5|" in ack


def test_ack_with_missing_fields():
    """Test ACK generation when MSH has missing optional fields."""
    # Create MSH with minimal fields
    message = "MSH|^~\\&|||||||ADT^A04|MSG00002|P|2.5\r"
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)

    generator = ACKGenerator()
    ack = generator.generate_success(msh)

    # Should still generate valid ACK with defaults
    assert "MSH|^~\\&" in ack
    assert "MSA|AA|MSG00002" in ack
    assert "GRAHAME|INTELLICARE|UNKNOWN|UNKNOWN" in ack


def test_build_simple_ack_default():
    """Test simple ACK builder with defaults."""
    ack = build_simple_ack()

    assert "MSH|^~\\&|GRAHAME|INTELLICARE" in ack
    assert "MSA|AA|UNKNOWN|Message accepted" in ack


def test_build_simple_ack_custom():
    """Test simple ACK builder with custom values."""
    ack = build_simple_ack(
        message_control_id="CUSTOM123",
        ack_code="AR",
        message_text="Custom error message"
    )

    assert "MSA|AR|CUSTOM123|Custom error message" in ack


def test_ack_format_is_parseable(sample_msh):
    """Test that generated ACK can be parsed back."""
    generator = ACKGenerator()
    ack = generator.generate_success(sample_msh)

    # Parse the ACK
    parser = HL7v2Parser(ack)

    # Verify it can be parsed
    assert parser.message_type == "ACK^A04"
    assert parser.has_segment("MSH")
    assert parser.has_segment("MSA")

    # Verify MSA fields
    msa_ack_code = parser.get_field("MSA", 1)
    msa_msg_ctrl_id = parser.get_field("MSA", 2)
    msa_text = parser.get_field("MSA", 3)

    assert msa_ack_code == "AA"
    assert msa_msg_ctrl_id == "MSG00001"
    assert msa_text == "Message accepted"


def test_ack_with_special_characters_in_message():
    """Test ACK generation with special characters in error message."""
    message = "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00003|P|2.5\r"
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)

    generator = ACKGenerator()
    error_msg = "Error: Patient name contains invalid character ^"
    ack = generator.generate_reject(msh, error_msg)

    # Verify special character is preserved
    assert error_msg in ack
    assert "MSA|AR|MSG00003" in ack

