"""Tests for HL7v2 REST endpoint."""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Mock redis module before importing
mock_redis_module = MagicMock()
mock_redis_module.asyncio = MagicMock()
mock_redis_module.asyncio.from_url = AsyncMock()
sys.modules['redis'] = mock_redis_module
sys.modules['redis.asyncio'] = mock_redis_module.asyncio

from grahame.api.app import app
from grahame.models.hl7v2_api_key import HL7v2APIKey


# Sample ADT^A04 message
SAMPLE_ADT_A04 = (
    "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
    "PID|1||12345^^^HOSPITAL^MR~11122233344^^^BR^CPF||Silva^João^Carlos||19800115|M|||"
    "Rua das Flores, 123^^São Paulo^SP^01234-567^BR||11987654321^PRN^PH|||||||2135-4^Pardo^HL70005|"
    "||||||||2186-5^Hispanic^HL70189\r"
    "PV1|1|I|WARD1^101^A^HOSPITAL||||||||||||||||VN123456|||||||||||||||||||HOSPITAL|||||20260224100000"
)

# Invalid message (missing patient ID)
INVALID_MESSAGE = (
    "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
    "PID|1||||Silva^João^Carlos||19800115|M"
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis = AsyncMock()
    redis.xadd = AsyncMock(return_value=b"1234567890-0")
    redis.close = AsyncMock()
    return redis


@pytest.fixture
def valid_api_key():
    return HL7v2APIKey(
        id=1,
        api_key="valid-test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=None,
        allowed_ips=None,
        rate_limit_per_minute=60,
        usage_count=0,
    )


def _mock_db_with_key(api_key: HL7v2APIKey):
    async def _provider():
        db = AsyncMock()
        result = AsyncMock()
        result.scalar_one_or_none.return_value = api_key
        db.execute.return_value = result
        yield db

    return _provider


def test_receive_adt_a04_success(client, mock_redis, valid_api_key):
    """Test successful ADT^A04 message processing."""
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=_mock_db_with_key(valid_api_key)):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=SAMPLE_ADT_A04,
                headers={
                    "Content-Type": "application/x-hl7-v2",
                    "X-API-Key": "valid-test-key-123",
                },
            )
    
    assert response.status_code == 200
    assert "MSH|" in response.text
    assert "MSA|AA|MSG00001" in response.text  # AA = Application Accept
    assert "ACK^A04" in response.text


def test_receive_adt_a04_invalid_message(client, mock_redis, valid_api_key):
    """Test ADT^A04 with invalid message (missing patient ID)."""
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=_mock_db_with_key(valid_api_key)):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=INVALID_MESSAGE,
                headers={
                    "Content-Type": "application/x-hl7-v2",
                    "X-API-Key": "valid-test-key-123",
                },
            )
    
    assert response.status_code == 400
    assert "MSH|" in response.text
    assert "MSA|AR|MSG00001" in response.text  # AR = Application Reject


def test_receive_adt_a04_malformed_message(client, mock_redis, valid_api_key):
    """Test ADT^A04 with malformed message."""
    malformed_message = "This is not an HL7v2 message"

    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=_mock_db_with_key(valid_api_key)):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=malformed_message,
                headers={
                    "Content-Type": "application/x-hl7-v2",
                    "X-API-Key": "valid-test-key-123",
                },
            )

    # Should return reject ACK (AR) for malformed message
    assert response.status_code == 400
    assert "MSH|" in response.text
    assert "MSA|AR|" in response.text  # AR = Application Reject


def test_receive_adt_a04_minimal_message(client, mock_redis, valid_api_key):
    """Test ADT^A04 with minimal message (no PV1)."""
    minimal_message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00002|P|2.5\r"
        "PID|1||12345^^^HOSPITAL^MR||Silva^João||19800115|M"
    )
    
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=_mock_db_with_key(valid_api_key)):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=minimal_message,
                headers={
                    "Content-Type": "application/x-hl7-v2",
                    "X-API-Key": "valid-test-key-123",
                },
            )
    
    assert response.status_code == 200
    assert "MSA|AA|MSG00002" in response.text


def test_receive_adt_a04_text_plain_content_type(client, mock_redis, valid_api_key):
    """Test ADT^A04 with text/plain content type."""
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=_mock_db_with_key(valid_api_key)):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=SAMPLE_ADT_A04,
                headers={
                    "Content-Type": "text/plain",
                    "X-API-Key": "valid-test-key-123",
                },
            )
    
    assert response.status_code == 200
    assert "MSA|AA|MSG00001" in response.text


def test_receive_adt_a04_redis_unavailable(client, valid_api_key):
    """Test ADT^A04 when Redis is unavailable (graceful degradation)."""
    # Don't mock Redis - let it fail gracefully
    with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=_mock_db_with_key(valid_api_key)):
        response = client.post(
            "/api/v1/hl7v2/adt-a04",
            content=SAMPLE_ADT_A04,
            headers={
                "Content-Type": "application/x-hl7-v2",
                "X-API-Key": "valid-test-key-123",
            },
        )
    
    # Should still return success ACK even if Redis fails
    assert response.status_code == 200
    assert "MSA|AA|MSG00001" in response.text


def test_receive_adt_a04_utf8_encoding(client, mock_redis, valid_api_key):
    """Test ADT^A04 with UTF-8 encoding (Brazilian characters)."""
    utf8_message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00003|P|2.5\r"
        "PID|1||12345^^^HOSPITAL^MR||José^João^André||19800115|M|||"
        "Rua São José, 123^^São Paulo^SP^01234-567^BR"
    )
    
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=_mock_db_with_key(valid_api_key)):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=utf8_message.encode("utf-8"),
                headers={
                    "Content-Type": "application/x-hl7-v2; charset=utf-8",
                    "X-API-Key": "valid-test-key-123",
                },
            )
    
    assert response.status_code == 200
    assert "MSA|AA|MSG00003" in response.text
