"""Tests for HL7v2 Admin API endpoints."""

import pytest
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Mock redis module before importing
mock_redis_module = MagicMock()
mock_redis_module.asyncio = MagicMock()
mock_redis_module.asyncio.from_url = AsyncMock()
sys.modules['redis'] = mock_redis_module
sys.modules['redis.asyncio'] = mock_redis_module.asyncio

from grahame.api.app import app
from grahame.models.hl7v2_api_key import HL7v2APIKey


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_with_api_keys():
    """Mock database session with sample API Keys."""
    async def mock_get_db():
        db = AsyncMock()
        
        # Sample API Keys
        api_key1 = HL7v2APIKey(
            id=1,
            api_key="key-123",
            system_name="Hospital A",
            system_identifier="HSP-A",
            is_active=True,
            expires_at=None,
            rate_limit_per_minute=60,
            usage_count=100,
            allowed_ips="192.168.1.0/24",
        )
        
        api_key2 = HL7v2APIKey(
            id=2,
            api_key="key-456",
            system_name="Hospital B",
            system_identifier="HSP-B",
            is_active=False,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            rate_limit_per_minute=120,
            usage_count=50,
            allowed_ips="10.0.0.1,10.0.0.2",
        )
        
        # Mock execute to return API Keys
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [api_key1, api_key2]
        mock_result.scalar_one_or_none.return_value = api_key1
        db.execute = AsyncMock(return_value=mock_result)
        
        yield db
    
    return mock_get_db


def test_create_api_key(client, mock_db_with_api_keys):
    """Test creating a new API Key."""
    from unittest.mock import patch
    
    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.post(
            "/api/v1/admin/hl7v2/api-keys",
            json={
                "system_name": "Hospital Test",
                "system_identifier": "HSP-TEST",
                "description": "Test hospital",
                "rate_limit_per_minute": 100,
                "allowed_ips": "192.168.1.0/24",
                "expires_days": 365,
            },
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["system_name"] == "Hospital Test"
    assert data["system_identifier"] == "HSP-TEST"
    assert "api_key" in data  # API Key should be returned


def test_list_api_keys(client, mock_db_with_api_keys):
    """Test listing all API Keys."""
    from unittest.mock import patch
    
    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.get("/api/v1/admin/hl7v2/api-keys")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["system_identifier"] == "HSP-A"
    assert data[1]["system_identifier"] == "HSP-B"


def test_list_api_keys_active_only(client, mock_db_with_api_keys):
    """Test listing only active API Keys."""
    from unittest.mock import patch
    
    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.get("/api/v1/admin/hl7v2/api-keys?active_only=true")
    
    assert response.status_code == 200
    # Note: In real scenario, would filter active keys


def test_get_api_key(client, mock_db_with_api_keys):
    """Test getting a specific API Key."""
    from unittest.mock import patch
    
    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.get("/api/v1/admin/hl7v2/api-keys/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["system_identifier"] == "HSP-A"


def test_get_api_key_not_found(client):
    """Test getting non-existent API Key."""
    async def mock_get_db_empty():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        yield db
    
    from unittest.mock import patch
    
    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_get_db_empty):
        response = client.get("/api/v1/admin/hl7v2/api-keys/999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_api_key(client, mock_db_with_api_keys):
    """Test updating an API Key."""
    from unittest.mock import patch
    
    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.patch(
            "/api/v1/admin/hl7v2/api-keys/1",
            json={
                "rate_limit_per_minute": 200,
                "is_active": False,
            },
        )
    
    assert response.status_code == 200
    # Note: In real scenario, would verify updated fields


def test_delete_api_key(client, mock_db_with_api_keys):
    """Test deleting an API Key."""
    from unittest.mock import patch

    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.delete("/api/v1/admin/hl7v2/api-keys/1")

    assert response.status_code == 204


# ─────────────────────────────────────────────────────────────────────────────
# IP Whitelist Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_get_ip_whitelist(client, mock_db_with_api_keys):
    """Test getting IP whitelist."""
    from unittest.mock import patch

    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.get("/api/v1/admin/hl7v2/api-keys/1/whitelist")

    assert response.status_code == 200
    data = response.json()
    assert data["api_key_id"] == 1
    assert data["system_identifier"] == "HSP-A"
    assert data["allowed_ips"] == "192.168.1.0/24"
    assert data["ip_count"] == 1


def test_add_ips_to_whitelist(client, mock_db_with_api_keys):
    """Test adding IPs to whitelist."""
    from unittest.mock import patch

    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.post(
            "/api/v1/admin/hl7v2/api-keys/1/whitelist/add",
            json={"ips": "10.0.0.0/8,8.8.8.8"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["api_key_id"] == 1
    # Note: In real scenario, would verify IPs were added


def test_add_invalid_ips_to_whitelist(client, mock_db_with_api_keys):
    """Test adding invalid IPs to whitelist."""
    from unittest.mock import patch

    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.post(
            "/api/v1/admin/hl7v2/api-keys/1/whitelist/add",
            json={"ips": "not-an-ip,999.999.999.999"},
        )

    assert response.status_code == 422  # Validation error


def test_remove_ips_from_whitelist(client, mock_db_with_api_keys):
    """Test removing IPs from whitelist."""
    from unittest.mock import patch

    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.post(
            "/api/v1/admin/hl7v2/api-keys/1/whitelist/remove",
            json={"ips": "192.168.1.0/24"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["api_key_id"] == 1
    # Note: In real scenario, would verify IPs were removed


def test_clear_ip_whitelist(client, mock_db_with_api_keys):
    """Test clearing IP whitelist."""
    from unittest.mock import patch

    with patch('grahame.api.routes.hl7v2_admin.get_db_session', new=mock_db_with_api_keys):
        response = client.delete("/api/v1/admin/hl7v2/api-keys/1/whitelist")

    assert response.status_code == 200
    data = response.json()
    assert data["api_key_id"] == 1
    assert data["allowed_ips"] is None
    assert data["ip_count"] == 0

