"""Tests for HL7v2 Audit Log Model."""

import pytest
from datetime import datetime, timezone

from grahame.models.hl7v2_audit import HL7v2AuditLog


def test_audit_log_creation_success():
    """Test creating audit log for successful request."""
    audit_log = HL7v2AuditLog(
        api_key_id=1,
        request_ip="192.168.1.100",
        request_user_agent="HL7v2-Client/1.0",
        message_control_id="MSG00001",
        message_type="ADT^A04",
        sending_application="HOSPITAL",
        sending_facility="FACILITY",
        raw_message="MSH|^~\\&|HOSPITAL|FACILITY|...",
        message_size_bytes=500,
        success=True,
        http_status_code=200,
        ack_code="AA",
        error_message=None,
        processing_time_ms=45,
        patient_id="patient-123",
        encounter_id="encounter-456",
    )
    
    assert audit_log.api_key_id == 1
    assert audit_log.request_ip == "192.168.1.100"
    assert audit_log.message_control_id == "MSG00001"
    assert audit_log.message_type == "ADT^A04"
    assert audit_log.success is True
    assert audit_log.http_status_code == 200
    assert audit_log.ack_code == "AA"
    assert audit_log.processing_time_ms == 45
    assert audit_log.patient_id == "patient-123"
    assert audit_log.encounter_id == "encounter-456"


def test_audit_log_creation_failure():
    """Test creating audit log for failed request."""
    audit_log = HL7v2AuditLog(
        api_key_id=1,
        request_ip="192.168.1.100",
        request_user_agent="HL7v2-Client/1.0",
        message_control_id="MSG00002",
        message_type="ADT^A04",
        sending_application="HOSPITAL",
        sending_facility="FACILITY",
        raw_message="MSH|^~\\&|HOSPITAL|FACILITY|...",
        message_size_bytes=500,
        success=False,
        http_status_code=400,
        ack_code="AR",
        error_message="Missing required field: PID-5 (Patient Name)",
        processing_time_ms=12,
        patient_id=None,
        encounter_id=None,
    )
    
    assert audit_log.success is False
    assert audit_log.http_status_code == 400
    assert audit_log.ack_code == "AR"
    assert audit_log.error_message == "Missing required field: PID-5 (Patient Name)"
    assert audit_log.patient_id is None
    assert audit_log.encounter_id is None


def test_audit_log_auth_failure():
    """Test creating audit log for authentication failure."""
    audit_log = HL7v2AuditLog(
        api_key_id=None,  # No API Key (auth failed)
        request_ip="192.168.1.200",
        request_user_agent="curl/7.68.0",
        message_control_id=None,
        message_type=None,
        sending_application=None,
        sending_facility=None,
        raw_message="MSH|^~\\&|...",
        message_size_bytes=100,
        success=False,
        http_status_code=401,
        ack_code=None,
        error_message="Invalid API Key",
        processing_time_ms=5,
        patient_id=None,
        encounter_id=None,
    )
    
    assert audit_log.api_key_id is None
    assert audit_log.success is False
    assert audit_log.http_status_code == 401
    assert audit_log.error_message == "Invalid API Key"


def test_audit_log_ipv6():
    """Test audit log with IPv6 address."""
    audit_log = HL7v2AuditLog(
        api_key_id=1,
        request_ip="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        request_user_agent="HL7v2-Client/1.0",
        message_control_id="MSG00003",
        message_type="ADT^A04",
        sending_application="HOSPITAL",
        sending_facility="FACILITY",
        raw_message="MSH|^~\\&|...",
        message_size_bytes=500,
        success=True,
        http_status_code=200,
        ack_code="AA",
        error_message=None,
        processing_time_ms=50,
    )
    
    assert audit_log.request_ip == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    assert len(audit_log.request_ip) <= 45  # Max IPv6 length


def test_audit_log_large_message():
    """Test audit log with large HL7v2 message."""
    large_message = "MSH|^~\\&|HOSPITAL|FACILITY|..." + ("X" * 10000)
    
    audit_log = HL7v2AuditLog(
        api_key_id=1,
        request_ip="192.168.1.100",
        request_user_agent="HL7v2-Client/1.0",
        message_control_id="MSG00004",
        message_type="ADT^A04",
        sending_application="HOSPITAL",
        sending_facility="FACILITY",
        raw_message=large_message,
        message_size_bytes=len(large_message.encode("utf-8")),
        success=True,
        http_status_code=200,
        ack_code="AA",
        error_message=None,
        processing_time_ms=150,
    )
    
    assert audit_log.message_size_bytes > 10000
    assert len(audit_log.raw_message) > 10000


def test_audit_log_utf8_message():
    """Test audit log with UTF-8 characters (Brazilian names)."""
    utf8_message = "MSH|^~\\&|HOSPITAL|FACILITY|...\rPID|1||12345||José^João^André||..."
    
    audit_log = HL7v2AuditLog(
        api_key_id=1,
        request_ip="192.168.1.100",
        request_user_agent="HL7v2-Client/1.0",
        message_control_id="MSG00005",
        message_type="ADT^A04",
        sending_application="HOSPITAL",
        sending_facility="FACILITY",
        raw_message=utf8_message,
        message_size_bytes=len(utf8_message.encode("utf-8")),
        success=True,
        http_status_code=200,
        ack_code="AA",
        error_message=None,
        processing_time_ms=55,
    )
    
    assert "José" in audit_log.raw_message
    assert "João" in audit_log.raw_message
    assert "André" in audit_log.raw_message


def test_audit_log_minimal_fields():
    """Test audit log with minimal required fields."""
    audit_log = HL7v2AuditLog(
        request_ip="192.168.1.100",
        raw_message="Invalid message",
        message_size_bytes=15,
        success=False,
        http_status_code=400,
    )
    
    assert audit_log.request_ip == "192.168.1.100"
    assert audit_log.raw_message == "Invalid message"
    assert audit_log.success is False
    assert audit_log.http_status_code == 400
    
    # Optional fields should be None
    assert audit_log.api_key_id is None
    assert audit_log.message_control_id is None
    assert audit_log.ack_code is None
    assert audit_log.patient_id is None

