"""Integration tests for HL7v2 end-to-end flow.

Tests the complete flow:
1. Parse HL7v2 message (ADT^A04)
2. Convert to FHIR resources (Patient + Encounter)
3. Publish events to Redis Stream
4. Generate ACK message
"""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# Mock redis module before importing
mock_redis_module = MagicMock()
mock_redis_module.asyncio = MagicMock()
# Set up a default from_url that will be overridden in tests
mock_redis_module.asyncio.from_url = AsyncMock()
sys.modules['redis'] = mock_redis_module
sys.modules['redis.asyncio'] = mock_redis_module.asyncio

from grahame.hl7v2.parser import HL7v2Parser
from grahame.hl7v2.segments import MSHSegment, PIDSegment, PV1Segment
from grahame.hl7v2.messages.adt_a04 import ADTMessage
from grahame.hl7v2.converters import PatientConverter, EncounterConverter
from grahame.hl7v2.ack import ACKGenerator
from grahame.events import HL7v2EventPublisher


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis = AsyncMock()
    redis.xadd = AsyncMock(return_value=b"1234567890-0")
    redis.close = AsyncMock()
    return redis


# Sample ADT^A04 message (Register Patient)
SAMPLE_ADT_A04 = (
    "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
    "PID|1||12345^^^HOSPITAL^MR~11122233344^^^BR^CPF||Silva^João^Carlos||19800115|M|||"
    "Rua das Flores, 123^^São Paulo^SP^01234-567^BR||11987654321^PRN^PH|||||||2135-4^Pardo^HL70005|"
    "||||||||2186-5^Hispanic^HL70189\r"
    "PV1|1|I|WARD1^101^A^HOSPITAL||||||||||||||||VN123456|||||||||||||||||||HOSPITAL|||||20260224100000"
)


@pytest.mark.asyncio
async def test_complete_adt_a04_flow(mock_redis):
    """Test complete ADT^A04 processing flow."""

    # Step 1: Parse HL7v2 message
    parser = HL7v2Parser(SAMPLE_ADT_A04)
    
    msh = MSHSegment.from_parser(parser)
    assert msh.message_type == "ADT^A04"
    assert msh.message_control_id == "MSG00001"
    
    pid = PIDSegment.from_parser(parser)
    assert len(pid.patient_id_list) == 2
    assert pid.patient_id_list[0]["id"] == "12345"
    assert pid.patient_id_list[0]["assigning_authority"] == "HOSPITAL"
    assert pid.patient_id_list[1]["id"] == "11122233344"
    assert pid.patient_id_list[1]["identifier_type"] == "CPF"
    assert pid.patient_name["family"] == "Silva"
    assert pid.patient_name["given"] == "João"
    
    pv1 = PV1Segment.from_parser(parser)
    # Note: patient_class is mapped (I → imp)
    assert pv1.patient_class == "imp"
    # Note: assigned_location is parsed as PL datatype (dict)
    assert pv1.assigned_location["point_of_care"] == "WARD1"
    assert pv1.assigned_location["room"] == "101"
    assert pv1.assigned_location["bed"] == "A"
    assert pv1.assigned_location["facility"] == "HOSPITAL"
    
    # Step 2: Create ADT^A04 message object
    adt_message = ADTMessage(msh=msh, pid=pid, pv1=pv1)

    # Validate message (returns tuple[bool, Optional[str]])
    is_valid, error_message = adt_message.validate()
    assert is_valid is True
    assert error_message is None
    
    # Step 3: Convert to FHIR resources
    patient_converter = PatientConverter()
    patient = patient_converter.convert(pid, msh)

    assert patient["resourceType"] == "Patient"
    assert patient["name"][0]["family"] == "Silva"
    assert patient["name"][0]["given"] == ["João", "Carlos"]
    assert patient["gender"] == "male"
    assert patient["birthDate"] == "1980-01-15"

    # Check CPF identifier
    cpf_identifier = next(
        (id for id in patient["identifier"] if id["type"]["coding"][0]["code"] == "CPF"),
        None
    )
    assert cpf_identifier is not None
    assert cpf_identifier["value"] == "11122233344"

    encounter_converter = EncounterConverter()
    encounter = encounter_converter.convert(pv1, msh, patient_id="patient-123")
    
    assert encounter["resourceType"] == "Encounter"
    assert encounter["status"] == "in-progress"
    assert encounter["class"]["code"] == "imp"  # I → imp (inpatient)
    assert encounter["subject"]["reference"] == "Patient/patient-123"
    
    # Step 4: Publish events to Redis
    # Use patch to mock aioredis.from_url in the hl7v2_publisher module
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        publisher = HL7v2EventPublisher("redis://localhost:6379")
        await publisher.connect()

        # Publish patient-created event
        result = await publisher.publish_patient_created(
            patient=patient,
            source_system="HOSPITAL:FACILITY",
            message_control_id="MSG00001",
        )
        assert result is True

        # Verify patient event was published
        assert mock_redis.xadd.call_count == 1
        call_args = mock_redis.xadd.call_args_list[0]
        assert call_args[0][0] == "intellicare:hl7v2:patient-created"
        event_data = call_args[0][1]
        assert event_data["event_type"] == "patient.created"
        assert event_data["resource_type"] == "Patient"
        assert event_data["source_system"] == "HOSPITAL:FACILITY"
        assert event_data["message_control_id"] == "MSG00001"

        # Publish encounter-created event
        result = await publisher.publish_encounter_created(
            encounter=encounter,
            patient_id="patient-123",
            source_system="HOSPITAL:FACILITY",
            message_control_id="MSG00001",
        )
        assert result is True

        # Verify encounter event was published
        assert mock_redis.xadd.call_count == 2
        call_args = mock_redis.xadd.call_args_list[1]
        assert call_args[0][0] == "intellicare:hl7v2:encounter-created"
        event_data = call_args[0][1]
        assert event_data["event_type"] == "encounter.created"
        assert event_data["resource_type"] == "Encounter"
        assert event_data["patient_id"] == "patient-123"

        await publisher.disconnect()
    
    # Step 5: Generate ACK message
    ack_generator = ACKGenerator()
    ack = ack_generator.generate_success(msh, message="Message accepted")

    assert "MSH|" in ack
    assert "MSA|AA|MSG00001" in ack
    assert "Message accepted" in ack

    # Verify ACK is parseable
    ack_parser = HL7v2Parser(ack)
    ack_msh = MSHSegment.from_parser(ack_parser)
    assert ack_msh.message_type == "ACK^A04"  # ACK with trigger event
    assert ack_msh.sending_application == "GRAHAME"  # Swapped from receiving
    assert ack_msh.receiving_application == "HOSPITAL"  # Swapped from sending


@pytest.mark.asyncio
async def test_integration_invalid_message(mock_redis):
    """Test integration flow with invalid message (missing required fields)."""

    # Message missing patient name (PID-5)
    invalid_message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00002|P|2.5\r"
        "PID|1||12345^^^HOSPITAL^MR||||||M\r"  # Missing name
        "PV1|1|I|WARD1^101^A^HOSPITAL"
    )

    parser = HL7v2Parser(invalid_message)
    msh = MSHSegment.from_parser(parser)
    pid = PIDSegment.from_parser(parser)
    pv1 = PV1Segment.from_parser(parser)

    adt_message = ADTMessage(msh=msh, pid=pid, pv1=pv1)

    # Validation should fail
    is_valid, error_message = adt_message.validate()
    assert is_valid is False
    assert error_message is not None
    assert "patient name" in error_message.lower()

    # Generate error ACK
    ack_generator = ACKGenerator()
    ack = ack_generator.generate_error(msh, error_message)

    assert "MSH|" in ack
    assert "MSA|AE|MSG00002" in ack  # AE = Application Error
    assert error_message in ack


@pytest.mark.asyncio
async def test_integration_minimal_message(mock_redis):
    """Test integration flow with minimal valid message (only required fields)."""

    minimal_message = (
        "MSH|^~\\&|SYS|FAC|GRAHAME|INTELLICARE|20260224120000||ADT^A04|MSG00003|P|2.5\r"
        "PID|1||999^^^SYS^MR||Doe^John||19900101|M\r"
        "PV1|1|O"  # Minimal PV1 - just patient class
    )

    parser = HL7v2Parser(minimal_message)
    msh = MSHSegment.from_parser(parser)
    pid = PIDSegment.from_parser(parser)
    pv1 = PV1Segment.from_parser(parser)

    # Validate
    adt_message = ADTMessage(msh=msh, pid=pid, pv1=pv1)
    is_valid, error_message = adt_message.validate()
    assert is_valid is True

    # Convert to FHIR
    patient_converter = PatientConverter()
    patient = patient_converter.convert(pid, msh)

    assert patient["resourceType"] == "Patient"
    assert patient["name"][0]["family"] == "Doe"
    assert patient["name"][0]["given"] == ["John"]
    assert patient["gender"] == "male"
    assert patient["birthDate"] == "1990-01-01"

    encounter_converter = EncounterConverter()
    encounter = encounter_converter.convert(pv1, msh, patient_id="patient-999")

    assert encounter["resourceType"] == "Encounter"
    assert encounter["class"]["code"] == "amb"  # O → amb (ambulatory)

    # Publish events
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        publisher = HL7v2EventPublisher("redis://localhost:6379")
        await publisher.connect()

        result = await publisher.publish_patient_created(
            patient=patient,
            source_system="SYS:FAC",
            message_control_id="MSG00003",
        )
        assert result is True

        await publisher.disconnect()

    # Generate ACK
    ack_generator = ACKGenerator()
    ack = ack_generator.generate_success(msh, message="Minimal message accepted")
    assert "MSA|AA|MSG00003" in ack


@pytest.mark.asyncio
async def test_integration_redis_failure(mock_redis):
    """Test integration flow when Redis publishing fails."""

    message = (
        "MSH|^~\\&|SYS|FAC|GRAHAME|INTELLICARE|20260224130000||ADT^A04|MSG00004|P|2.5\r"
        "PID|1||888^^^SYS^MR||Test^Patient||19850515|F\r"
        "PV1|1|E"  # Emergency
    )

    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)
    pid = PIDSegment.from_parser(parser)
    pv1 = PV1Segment.from_parser(parser)

    # Convert to FHIR
    patient_converter = PatientConverter()
    patient = patient_converter.convert(pid, msh)

    # Mock Redis to raise an exception
    mock_redis_error = AsyncMock()
    mock_redis_error.xadd = AsyncMock(side_effect=Exception("Redis connection failed"))
    mock_redis_error.close = AsyncMock()

    # Publishing should fail gracefully (return False, not raise exception)
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis_error)):
        publisher = HL7v2EventPublisher("redis://localhost:6379")
        await publisher.connect()

        result = await publisher.publish_patient_created(
            patient=patient,
            source_system="SYS:FAC",
            message_control_id="MSG00004",
        )

        # Should return False but not raise exception
        assert result is False

        await publisher.disconnect()

    # Message processing should continue even if event publishing fails
    # Generate ACK anyway
    ack_generator = ACKGenerator()
    ack = ack_generator.generate_success(msh, message="Message accepted")
    assert "MSA|AA|MSG00004" in ack

