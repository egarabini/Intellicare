"""Pydantic schemas for HL7v2 Audit Log API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HL7v2AuditLogResponse(BaseModel):
    """Response schema for audit log entry."""
    
    id: int = Field(..., description="Audit log ID")
    api_key_id: int = Field(..., description="API Key ID")
    system_identifier: Optional[str] = Field(None, description="System identifier from API Key")
    request_ip: str = Field(..., description="Client IP address")
    request_user_agent: Optional[str] = Field(None, description="User agent")
    message_control_id: Optional[str] = Field(None, description="HL7v2 message control ID")
    message_type: Optional[str] = Field(None, description="HL7v2 message type (e.g., ADT^A04)")
    sending_application: Optional[str] = Field(None, description="Sending application")
    sending_facility: Optional[str] = Field(None, description="Sending facility")
    message_size_bytes: int = Field(..., description="Message size in bytes")
    success: bool = Field(..., description="Whether processing was successful")
    http_status_code: int = Field(..., description="HTTP status code")
    ack_code: Optional[str] = Field(None, description="ACK code (AA, AR, AE)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    patient_id: Optional[str] = Field(None, description="FHIR Patient ID")
    encounter_id: Optional[str] = Field(None, description="FHIR Encounter ID")
    created_at: datetime = Field(..., description="Timestamp when log was created")
    
    class Config:
        from_attributes = True


class HL7v2AuditLogDetailResponse(HL7v2AuditLogResponse):
    """Response schema for audit log entry with raw message."""
    
    raw_message: str = Field(..., description="Raw HL7v2 message")


class HL7v2AuditLogListResponse(BaseModel):
    """Response schema for list of audit logs."""
    
    total: int = Field(..., description="Total number of audit logs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    logs: list[HL7v2AuditLogResponse] = Field(..., description="List of audit logs")


class HL7v2AuditStatsResponse(BaseModel):
    """Response schema for audit statistics."""
    
    total_requests: int = Field(..., description="Total number of requests")
    successful_requests: int = Field(..., description="Number of successful requests")
    failed_requests: int = Field(..., description="Number of failed requests")
    success_rate: float = Field(..., description="Success rate (0-100)")
    avg_processing_time_ms: float = Field(..., description="Average processing time in ms")
    total_bytes_processed: int = Field(..., description="Total bytes processed")
    unique_systems: int = Field(..., description="Number of unique systems")
    by_status_code: dict[int, int] = Field(..., description="Requests by HTTP status code")
    by_ack_code: dict[str, int] = Field(..., description="Requests by ACK code")
    by_message_type: dict[str, int] = Field(..., description="Requests by message type")


class HL7v2AuditFilterParams(BaseModel):
    """Query parameters for filtering audit logs."""
    
    api_key_id: Optional[int] = Field(None, description="Filter by API Key ID")
    success: Optional[bool] = Field(None, description="Filter by success status")
    http_status_code: Optional[int] = Field(None, description="Filter by HTTP status code")
    ack_code: Optional[str] = Field(None, description="Filter by ACK code")
    message_type: Optional[str] = Field(None, description="Filter by message type")
    sending_application: Optional[str] = Field(None, description="Filter by sending application")
    sending_facility: Optional[str] = Field(None, description="Filter by sending facility")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")
    sort_by: str = Field("created_at", description="Sort by field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

