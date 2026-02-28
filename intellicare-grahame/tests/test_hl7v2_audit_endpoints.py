"""Tests for HL7v2 Audit Log API endpoints."""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from grahame.models.hl7v2_api_key import HL7v2APIKey
from grahame.models.hl7v2_audit import HL7v2AuditLog


@pytest.fixture
async def api_key(db_session):
    """Create test API Key."""
    api_key = HL7v2APIKey(
        api_key="test_key_123",
        system_name="Test Hospital",
        system_identifier="TEST-001",
        is_active=True,
        rate_limit_per_minute=100,
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    return api_key


@pytest.fixture
async def audit_logs(db_session, api_key):
    """Create test audit logs."""
    logs = []
    
    # Successful log
    log1 = HL7v2AuditLog(
        api_key_id=api_key.id,
        request_ip="192.168.1.100",
        request_user_agent="Test Agent",
        message_control_id="MSG001",
        message_type="ADT^A04",
        sending_application="TEST_APP",
        sending_facility="TEST_FAC",
        raw_message="MSH|^~\\&|TEST_APP|TEST_FAC|...",
        message_size_bytes=500,
        success=True,
        http_status_code=200,
        ack_code="AA",
        processing_time_ms=150,
        patient_id="Patient/123",
        encounter_id="Encounter/456",
    )
    logs.append(log1)
    
    # Failed log
    log2 = HL7v2AuditLog(
        api_key_id=api_key.id,
        request_ip="192.168.1.101",
        request_user_agent="Test Agent",
        message_control_id="MSG002",
        message_type="ADT^A04",
        sending_application="TEST_APP",
        sending_facility="TEST_FAC",
        raw_message="MSH|^~\\&|TEST_APP|TEST_FAC|...",
        message_size_bytes=450,
        success=False,
        http_status_code=400,
        ack_code="AR",
        error_message="Validation failed",
        processing_time_ms=50,
    )
    logs.append(log2)
    
    # Another successful log
    log3 = HL7v2AuditLog(
        api_key_id=api_key.id,
        request_ip="192.168.1.100",
        request_user_agent="Test Agent",
        message_control_id="MSG003",
        message_type="ADT^A04",
        sending_application="TEST_APP",
        sending_facility="TEST_FAC",
        raw_message="MSH|^~\\&|TEST_APP|TEST_FAC|...",
        message_size_bytes=520,
        success=True,
        http_status_code=200,
        ack_code="AA",
        processing_time_ms=180,
        patient_id="Patient/789",
    )
    logs.append(log3)
    
    for log in logs:
        db_session.add(log)
    
    await db_session.commit()
    
    for log in logs:
        await db_session.refresh(log)
    
    return logs


@pytest.mark.asyncio
async def test_list_audit_logs(client, audit_logs):
    """Test listing audit logs."""
    response = client.get("/api/v1/admin/hl7v2/audit/logs")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 50
    assert len(data["logs"]) == 3


@pytest.mark.asyncio
async def test_list_audit_logs_filter_by_success(client, audit_logs):
    """Test filtering audit logs by success status."""
    response = client.get("/api/v1/admin/hl7v2/audit/logs?success=true")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 2
    assert all(log["success"] is True for log in data["logs"])


@pytest.mark.asyncio
async def test_list_audit_logs_filter_by_http_status(client, audit_logs):
    """Test filtering audit logs by HTTP status code."""
    response = client.get("/api/v1/admin/hl7v2/audit/logs?http_status_code=400")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 1
    assert data["logs"][0]["http_status_code"] == 400


@pytest.mark.asyncio
async def test_list_audit_logs_pagination(client, audit_logs):
    """Test pagination of audit logs."""
    response = client.get("/api/v1/admin/hl7v2/audit/logs?page=1&page_size=2")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["logs"]) == 2


@pytest.mark.asyncio
async def test_get_audit_log_detail(client, audit_logs):
    """Test getting audit log detail."""
    log_id = audit_logs[0].id
    response = client.get(f"/api/v1/admin/hl7v2/audit/logs/{log_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == log_id
    assert data["message_control_id"] == "MSG001"
    assert "raw_message" in data
    assert data["raw_message"] == "MSH|^~\\&|TEST_APP|TEST_FAC|..."


@pytest.mark.asyncio
async def test_get_audit_log_not_found(client):
    """Test getting non-existent audit log."""
    response = client.get("/api/v1/admin/hl7v2/audit/logs/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_audit_stats(client, audit_logs):
    """Test getting audit statistics."""
    response = client.get("/api/v1/admin/hl7v2/audit/stats")

    assert response.status_code == 200
    data = response.json()

    assert data["total_requests"] == 3
    assert data["successful_requests"] == 2
    assert data["failed_requests"] == 1
    assert data["success_rate"] == pytest.approx(66.67, rel=0.1)
    assert data["avg_processing_time_ms"] > 0
    assert data["total_bytes_processed"] == 1470  # 500 + 450 + 520
    assert data["unique_systems"] == 1

    # Check by_status_code
    assert data["by_status_code"]["200"] == 2
    assert data["by_status_code"]["400"] == 1

    # Check by_ack_code
    assert data["by_ack_code"]["AA"] == 2
    assert data["by_ack_code"]["AR"] == 1

    # Check by_message_type
    assert data["by_message_type"]["ADT^A04"] == 3


@pytest.mark.asyncio
async def test_get_audit_stats_filtered(client, audit_logs):
    """Test getting audit statistics with filters."""
    response = client.get("/api/v1/admin/hl7v2/audit/stats?success=true")

    assert response.status_code == 200
    data = response.json()

    assert data["total_requests"] == 2
    assert data["successful_requests"] == 2
    assert data["failed_requests"] == 0
    assert data["success_rate"] == 100.0

