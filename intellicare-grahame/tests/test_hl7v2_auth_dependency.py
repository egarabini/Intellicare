"""Tests for HL7v2 Authentication Dependency."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from grahame.api.dependencies.hl7v2_auth import validate_hl7v2_api_key, update_api_key_usage
from grahame.models.hl7v2_api_key import HL7v2APIKey


@pytest.fixture
def mock_request():
    """Create mock FastAPI request."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = "192.168.1.100"
    request.app = MagicMock()
    request.app.state = MagicMock()
    return request


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    return db


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


@pytest.mark.asyncio
async def test_validate_api_key_missing_header(mock_request, mock_db):
    """Test validation fails when X-API-Key header is missing."""
    with pytest.raises(HTTPException) as exc_info:
        await validate_hl7v2_api_key(
            request=mock_request,
            x_api_key=None,
            db=mock_db,
        )
    
    assert exc_info.value.status_code == 401
    assert "Missing X-API-Key header" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_api_key_invalid_key(mock_request, mock_db):
    """Test validation fails with invalid API Key."""
    # Mock database to return None (key not found)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await validate_hl7v2_api_key(
            request=mock_request,
            x_api_key="invalid-key",
            db=mock_db,
        )

    assert exc_info.value.status_code == 401
    assert "Invalid API Key" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_api_key_inactive(mock_request, mock_db):
    """Test validation fails with inactive API Key."""
    inactive_key = HL7v2APIKey(
        id=1,
        api_key="inactive-key",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=False,  # Inactive
        expires_at=None,
        rate_limit_per_minute=60,
        usage_count=0,
    )

    # Mock database to return inactive key
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = inactive_key
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await validate_hl7v2_api_key(
            request=mock_request,
            x_api_key="inactive-key",
            db=mock_db,
        )

    assert exc_info.value.status_code == 401
    assert "inactive or expired" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_api_key_expired(mock_request, mock_db):
    """Test validation fails with expired API Key."""
    expired_key = HL7v2APIKey(
        id=1,
        api_key="expired-key",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        rate_limit_per_minute=60,
        usage_count=0,
    )

    # Mock database to return expired key
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expired_key
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await validate_hl7v2_api_key(
            request=mock_request,
            x_api_key="expired-key",
            db=mock_db,
        )

    assert exc_info.value.status_code == 401
    assert "inactive or expired" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_api_key_ip_not_whitelisted(mock_request, mock_db):
    """Test validation fails when IP is not whitelisted."""
    key_with_whitelist = HL7v2APIKey(
        id=1,
        api_key="whitelist-key",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=None,
        allowed_ips="192.168.1.1,192.168.1.2",  # Whitelist doesn't include 192.168.1.100
        rate_limit_per_minute=60,
        usage_count=0,
    )

    # Mock database to return key with whitelist
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = key_with_whitelist
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await validate_hl7v2_api_key(
            request=mock_request,
            x_api_key="whitelist-key",
            db=mock_db,
        )

    assert exc_info.value.status_code == 403
    assert "not whitelisted" in exc_info.value.detail
    assert "192.168.1.100" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_api_key_success(mock_request, mock_db, valid_api_key):
    """Test successful API Key validation."""
    # Mock database to return valid key
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = valid_api_key
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await validate_hl7v2_api_key(
        request=mock_request,
        x_api_key="valid-test-key-123",
        db=mock_db,
    )

    assert result == valid_api_key
    assert result.system_identifier == "TEST-001"


@pytest.mark.asyncio
async def test_validate_api_key_with_whitelist_success(mock_request, mock_db):
    """Test successful validation with IP in whitelist."""
    key_with_whitelist = HL7v2APIKey(
        id=1,
        api_key="whitelist-key",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=None,
        allowed_ips="192.168.1.100,192.168.1.101",  # Includes request IP
        rate_limit_per_minute=60,
        usage_count=0,
    )

    # Mock database to return key with whitelist
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = key_with_whitelist
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await validate_hl7v2_api_key(
        request=mock_request,
        x_api_key="whitelist-key",
        db=mock_db,
    )

    assert result == key_with_whitelist


@pytest.mark.asyncio
async def test_update_api_key_usage(mock_db, valid_api_key):
    """Test updating API Key usage statistics."""
    initial_usage_count = valid_api_key.usage_count
    initial_last_used = valid_api_key.last_used_at
    
    await update_api_key_usage(valid_api_key, mock_db)
    
    # Check that usage was updated
    assert valid_api_key.usage_count == initial_usage_count + 1
    assert valid_api_key.last_used_at is not None
    assert valid_api_key.last_used_at != initial_last_used
    
    # Check that commit was called
    mock_db.commit.assert_called_once()

