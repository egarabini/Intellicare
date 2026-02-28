"""Tests for HL7v2 API Key Model."""

import pytest
from datetime import datetime, timedelta, timezone

from grahame.models.hl7v2_api_key import HL7v2APIKey


def test_generate_api_key():
    """Test API Key generation."""
    api_key = HL7v2APIKey.generate_api_key()
    
    assert api_key is not None
    assert len(api_key) > 0
    assert isinstance(api_key, str)
    
    # Generate another key - should be different
    api_key2 = HL7v2APIKey.generate_api_key()
    assert api_key != api_key2


def test_api_key_is_valid_active():
    """Test that active API Key without expiration is valid."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=None,
    )
    
    assert api_key.is_valid() is True


def test_api_key_is_valid_inactive():
    """Test that inactive API Key is invalid."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=False,
        expires_at=None,
    )
    
    assert api_key.is_valid() is False


def test_api_key_is_valid_expired():
    """Test that expired API Key is invalid."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired yesterday
    )
    
    assert api_key.is_valid() is False


def test_api_key_is_valid_not_expired():
    """Test that non-expired API Key is valid."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),  # Expires in 30 days
    )
    
    assert api_key.is_valid() is True


def test_is_ip_allowed_no_whitelist():
    """Test that all IPs are allowed when no whitelist is configured."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        allowed_ips=None,
    )
    
    assert api_key.is_ip_allowed("192.168.1.1") is True
    assert api_key.is_ip_allowed("10.0.0.1") is True
    assert api_key.is_ip_allowed("8.8.8.8") is True


def test_is_ip_allowed_with_whitelist():
    """Test IP whitelist validation."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        allowed_ips="192.168.1.1,192.168.1.2,10.0.0.1",
    )
    
    # Allowed IPs
    assert api_key.is_ip_allowed("192.168.1.1") is True
    assert api_key.is_ip_allowed("192.168.1.2") is True
    assert api_key.is_ip_allowed("10.0.0.1") is True
    
    # Not allowed IPs
    assert api_key.is_ip_allowed("192.168.1.3") is False
    assert api_key.is_ip_allowed("8.8.8.8") is False


def test_is_ip_allowed_with_whitespace():
    """Test IP whitelist with whitespace in the list."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        allowed_ips="192.168.1.1, 192.168.1.2 , 10.0.0.1",  # With spaces
    )
    
    # Should still work (spaces are stripped)
    assert api_key.is_ip_allowed("192.168.1.1") is True
    assert api_key.is_ip_allowed("192.168.1.2") is True
    assert api_key.is_ip_allowed("10.0.0.1") is True


def test_api_key_defaults():
    """Test default values for API Key."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,  # Explicitly set since defaults only apply on DB insert
        rate_limit_per_minute=60,
        usage_count=0,
    )

    # Check defaults
    assert api_key.is_active is True
    assert api_key.expires_at is None
    assert api_key.rate_limit_per_minute == 60
    assert api_key.allowed_ips is None
    assert api_key.usage_count == 0
    assert api_key.last_used_at is None


def test_api_key_creation_with_all_fields():
    """Test creating API Key with all fields."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=365)

    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Hospital São Paulo",
        system_identifier="HSP-TASY",
        description="Sistema Tasy do Hospital São Paulo",
        is_active=True,
        expires_at=expires,
        rate_limit_per_minute=120,
        allowed_ips="192.168.1.1,192.168.1.2",
        created_by="admin@intellicare.com",
        notes="Criado para integração inicial",
    )

    assert api_key.api_key == "test-key-123"
    assert api_key.system_name == "Hospital São Paulo"
    assert api_key.system_identifier == "HSP-TASY"
    assert api_key.description == "Sistema Tasy do Hospital São Paulo"
    assert api_key.is_active is True
    assert api_key.expires_at == expires
    assert api_key.rate_limit_per_minute == 120
    assert api_key.allowed_ips == "192.168.1.1,192.168.1.2"
    assert api_key.created_by == "admin@intellicare.com"
    assert api_key.notes == "Criado para integração inicial"


def test_is_ip_allowed_cidr_notation():
    """Test IP whitelist with CIDR notation."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        allowed_ips="192.168.1.0/24,10.0.0.0/8",  # CIDR notation
    )

    # IPs within 192.168.1.0/24
    assert api_key.is_ip_allowed("192.168.1.1") is True
    assert api_key.is_ip_allowed("192.168.1.100") is True
    assert api_key.is_ip_allowed("192.168.1.255") is True

    # IPs within 10.0.0.0/8
    assert api_key.is_ip_allowed("10.0.0.1") is True
    assert api_key.is_ip_allowed("10.255.255.255") is True

    # IPs outside the ranges
    assert api_key.is_ip_allowed("192.168.2.1") is False
    assert api_key.is_ip_allowed("11.0.0.1") is False
    assert api_key.is_ip_allowed("8.8.8.8") is False


def test_is_ip_allowed_mixed_cidr_and_individual():
    """Test IP whitelist with mix of CIDR and individual IPs."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        allowed_ips="192.168.1.0/24,8.8.8.8,1.1.1.1",  # Mix of CIDR and individual
    )

    # IPs within CIDR range
    assert api_key.is_ip_allowed("192.168.1.50") is True

    # Individual IPs
    assert api_key.is_ip_allowed("8.8.8.8") is True
    assert api_key.is_ip_allowed("1.1.1.1") is True

    # Not allowed
    assert api_key.is_ip_allowed("8.8.4.4") is False
    assert api_key.is_ip_allowed("192.168.2.1") is False


def test_is_ip_allowed_ipv6():
    """Test IP whitelist with IPv6 addresses."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        allowed_ips="2001:db8::/32,::1",  # IPv6 CIDR and loopback
    )

    # IPv6 within range
    assert api_key.is_ip_allowed("2001:db8::1") is True
    assert api_key.is_ip_allowed("2001:db8:ffff:ffff:ffff:ffff:ffff:ffff") is True

    # IPv6 loopback
    assert api_key.is_ip_allowed("::1") is True

    # Not allowed
    assert api_key.is_ip_allowed("2001:db9::1") is False
    assert api_key.is_ip_allowed("::2") is False


def test_is_ip_allowed_invalid_ip():
    """Test that invalid IP addresses are rejected."""
    api_key = HL7v2APIKey(
        api_key="test-key-123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        allowed_ips="192.168.1.0/24",
    )

    # Invalid IP formats should return False
    assert api_key.is_ip_allowed("not-an-ip") is False
    assert api_key.is_ip_allowed("999.999.999.999") is False
    assert api_key.is_ip_allowed("") is False

