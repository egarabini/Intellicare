"""Tests for HL7v2 Event Publisher."""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# Mock redis module before importing HL7v2EventPublisher
mock_redis_module = MagicMock()
mock_redis_module.asyncio = MagicMock()
sys.modules['redis'] = mock_redis_module
sys.modules['redis.asyncio'] = mock_redis_module.asyncio

from grahame.events import HL7v2EventPublisher


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.xadd = AsyncMock(return_value=b"1234567890-0")
    redis.close = AsyncMock()
    return redis


@pytest.fixture
async def publisher(mock_redis):
    """Create event publisher with mocked Redis."""
    # Mock the from_url function to return our mock redis
    mock_redis_module.asyncio.from_url = AsyncMock(return_value=mock_redis)

    publisher = HL7v2EventPublisher("redis://localhost:6379")
    await publisher.connect()

    yield publisher

    await publisher.disconnect()


@pytest.mark.asyncio
async def test_connect_to_redis(mock_redis):
    """Test connecting to Redis."""
    mock_redis_module.asyncio.from_url = AsyncMock(return_value=mock_redis)

    publisher = HL7v2EventPublisher("redis://localhost:6379")
    await publisher.connect()

    assert publisher._redis is not None
    mock_redis_module.asyncio.from_url.assert_called_once()


@pytest.mark.asyncio
async def test_publish_patient_created(publisher, mock_redis):
    """Test publishing patient-created event."""
    patient = {
        "resourceType": "Patient",
        "id": "patient-123",
        "name": [{"family": "Silva", "given": ["João"]}],
    }
    
    result = await publisher.publish_patient_created(
        patient=patient,
        source_system="HOSPITAL:FACILITY",
        message_control_id="MSG00001",
    )
    
    assert result is True
    
    # Verify Redis xadd was called
    mock_redis.xadd.assert_called_once()
    call_args = mock_redis.xadd.call_args
    
    # Check stream name
    assert call_args[0][0] == "intellicare:hl7v2:patient-created"
    
    # Check event data
    event_data = call_args[0][1]
    assert event_data["event_type"] == "patient.created"
    assert event_data["resource_type"] == "Patient"
    assert event_data["resource_id"] == "patient-123"
    assert event_data["source_system"] == "HOSPITAL:FACILITY"
    assert event_data["message_control_id"] == "MSG00001"
    assert "timestamp" in event_data
    
    # Check maxlen parameter
    assert call_args[1]["maxlen"] == 10_000


@pytest.mark.asyncio
async def test_publish_encounter_created(publisher, mock_redis):
    """Test publishing encounter-created event."""
    encounter = {
        "resourceType": "Encounter",
        "id": "encounter-456",
        "status": "in-progress",
        "class": {"code": "imp"},
    }
    
    result = await publisher.publish_encounter_created(
        encounter=encounter,
        patient_id="patient-123",
        source_system="HOSPITAL:FACILITY",
        message_control_id="MSG00001",
    )
    
    assert result is True
    
    # Verify Redis xadd was called
    mock_redis.xadd.assert_called_once()
    call_args = mock_redis.xadd.call_args
    
    # Check stream name
    assert call_args[0][0] == "intellicare:hl7v2:encounter-created"
    
    # Check event data
    event_data = call_args[0][1]
    assert event_data["event_type"] == "encounter.created"
    assert event_data["resource_type"] == "Encounter"
    assert event_data["resource_id"] == "encounter-456"
    assert event_data["patient_id"] == "patient-123"
    assert event_data["source_system"] == "HOSPITAL:FACILITY"
    assert event_data["message_control_id"] == "MSG00001"
    assert "timestamp" in event_data


@pytest.mark.asyncio
async def test_publish_without_redis_connection():
    """Test publishing when Redis is not connected."""
    publisher = HL7v2EventPublisher("redis://localhost:6379")
    # Don't call connect()
    
    patient = {"resourceType": "Patient", "id": "patient-123"}
    
    result = await publisher.publish_patient_created(
        patient=patient,
        source_system="HOSPITAL:FACILITY",
        message_control_id="MSG00001",
    )
    
    # Should return False but not raise exception
    assert result is False


@pytest.mark.asyncio
async def test_publish_handles_redis_error(publisher, mock_redis):
    """Test that publish handles Redis errors gracefully."""
    # Make xadd raise an exception
    mock_redis.xadd = AsyncMock(side_effect=Exception("Redis error"))
    
    patient = {"resourceType": "Patient", "id": "patient-123"}
    
    result = await publisher.publish_patient_created(
        patient=patient,
        source_system="HOSPITAL:FACILITY",
        message_control_id="MSG00001",
    )
    
    # Should return False but not raise exception
    assert result is False


@pytest.mark.asyncio
async def test_disconnect_from_redis(publisher, mock_redis):
    """Test disconnecting from Redis."""
    await publisher.disconnect()
    
    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_event_timestamp_is_iso_format(publisher, mock_redis):
    """Test that event timestamp is in ISO format."""
    patient = {"resourceType": "Patient", "id": "patient-123"}
    
    before = datetime.now(timezone.utc)
    await publisher.publish_patient_created(
        patient=patient,
        source_system="HOSPITAL:FACILITY",
        message_control_id="MSG00001",
    )
    after = datetime.now(timezone.utc)
    
    # Get the timestamp from the call
    call_args = mock_redis.xadd.call_args
    event_data = call_args[0][1]
    timestamp_str = event_data["timestamp"]
    
    # Parse timestamp
    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    
    # Verify it's within the expected range
    assert before <= timestamp <= after

