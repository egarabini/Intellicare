"""Integration tests for HL7v2 endpoint with API Key authentication."""

import pytest
import sys
from datetime import datetime, timedelta, timezone
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
    "PID|1||12345^^^HOSPITAL^MR||Silva^João||19800115|M\r"
    "PV1|1|I|WARD1^101^A^HOSPITAL||||||||||||||||VN123456"
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
    """Create valid API Key."""
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


@pytest.fixture
def mock_db_session(valid_api_key):
    """Mock database session that returns valid API Key."""
    async def mock_session():
        db = AsyncMock()
        
        # Mock execute to return valid API Key
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = valid_api_key
        db.execute.return_value = mock_result
        
        yield db
    
    return mock_session


def test_endpoint_without_api_key(client, mock_redis):
    """Test endpoint returns 401 when API Key is missing."""
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        response = client.post(
            "/api/v1/hl7v2/adt-a04",
            content=SAMPLE_ADT_A04,
            headers={"Content-Type": "application/x-hl7-v2"},
            # No X-API-Key header
        )
    
    assert response.status_code == 401
    assert "Missing X-API-Key header" in response.json()["detail"]


def test_endpoint_with_invalid_api_key(client, mock_redis):
    """Test endpoint returns 401 with invalid API Key."""
    # Mock database to return None (key not found)
    async def mock_get_db():
        db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        yield db
    
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=mock_get_db):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=SAMPLE_ADT_A04,
                headers={
                    "Content-Type": "application/x-hl7-v2",
                    "X-API-Key": "invalid-key-123",
                },
            )
    
    assert response.status_code == 401
    assert "Invalid API Key" in response.json()["detail"]


def test_endpoint_with_inactive_api_key(client, mock_redis):
    """Test endpoint returns 401 with inactive API Key."""
    inactive_key = HL7v2APIKey(
        id=1,
        api_key="inactive-key",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=False,  # Inactive
        expires_at=None,
    )
    
    # Mock database to return inactive key
    async def mock_get_db():
        db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = inactive_key
        db.execute.return_value = mock_result
        yield db
    
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=mock_get_db):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=SAMPLE_ADT_A04,
                headers={
                    "Content-Type": "application/x-hl7-v2",
                    "X-API-Key": "inactive-key",
                },
            )
    
    assert response.status_code == 401
    assert "inactive or expired" in response.json()["detail"]


def test_endpoint_with_expired_api_key(client, mock_redis):
    """Test endpoint returns 401 with expired API Key."""
    expired_key = HL7v2APIKey(
        id=1,
        api_key="expired-key",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
    )
    
    # Mock database to return expired key
    async def mock_get_db():
        db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = expired_key
        db.execute.return_value = mock_result
        yield db
    
    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=mock_get_db):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=SAMPLE_ADT_A04,
                headers={
                    "Content-Type": "application/x-hl7-v2",
                    "X-API-Key": "expired-key",
                },
            )
    
    assert response.status_code == 401
    assert "inactive or expired" in response.json()["detail"]


def test_endpoint_with_ip_not_whitelisted(client, mock_redis):
    """Test endpoint returns 403 when IP is not whitelisted."""
    key_with_whitelist = HL7v2APIKey(
        id=1,
        api_key="whitelist-key",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=None,
        allowed_ips="192.168.1.1,192.168.1.2",  # Doesn't include testclient IP
    )

    # Mock database to return key with whitelist
    async def mock_get_db():
        db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = key_with_whitelist
        db.execute.return_value = mock_result
        yield db

    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=mock_get_db):
            response = client.post(
                "/api/v1/hl7v2/adt-a04",
                content=SAMPLE_ADT_A04,
                headers={
                    "Content-Type": "application/x-hl7-v2",
                    "X-API-Key": "whitelist-key",
                },
            )

    assert response.status_code == 403
    assert "not whitelisted" in response.json()["detail"]


def test_endpoint_with_valid_api_key_success(client, mock_redis, valid_api_key):
    """Test successful request with valid API Key."""
    # Mock database to return valid key
    async def mock_get_db():
        db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = valid_api_key
        db.execute.return_value = mock_result
        yield db

    with patch('grahame.events.hl7v2_publisher.aioredis.from_url', new=AsyncMock(return_value=mock_redis)):
        with patch('grahame.api.dependencies.hl7v2_auth.get_db_session', new=mock_get_db):
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
    assert "MSA|AA|MSG00001" in response.text  # Success ACK
