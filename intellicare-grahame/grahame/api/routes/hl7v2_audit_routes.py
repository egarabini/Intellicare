"""HL7v2 Audit Log API Routes.

Este módulo fornece endpoints REST para consultar e analisar audit logs de mensagens HL7v2.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from grahame.api.dependencies import get_db_session
from grahame.api.schemas.hl7v2_audit import (
    HL7v2AuditLogResponse,
    HL7v2AuditLogDetailResponse,
    HL7v2AuditLogListResponse,
    HL7v2AuditStatsResponse,
)
from grahame.models.hl7v2_audit import HL7v2AuditLog
from grahame.models.hl7v2_api_key import HL7v2APIKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/hl7v2/audit", tags=["HL7v2 Audit"])


@router.get(
    "/logs",
    response_model=HL7v2AuditLogListResponse,
    summary="List audit logs",
    description="Get paginated list of HL7v2 audit logs with optional filters.",
)
async def list_audit_logs(
    db: AsyncSession = Depends(get_db_session),
    api_key_id: Optional[int] = Query(None, description="Filter by API Key ID"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    http_status_code: Optional[int] = Query(None, description="Filter by HTTP status code"),
    ack_code: Optional[str] = Query(None, description="Filter by ACK code"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    sending_application: Optional[str] = Query(None, description="Filter by sending application"),
    sending_facility: Optional[str] = Query(None, description="Filter by sending facility"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
) -> HL7v2AuditLogListResponse:
    """List audit logs with pagination and filters."""
    
    # Build query with filters
    filters = []
    
    if api_key_id is not None:
        filters.append(HL7v2AuditLog.api_key_id == api_key_id)
    if success is not None:
        filters.append(HL7v2AuditLog.success == success)
    if http_status_code is not None:
        filters.append(HL7v2AuditLog.http_status_code == http_status_code)
    if ack_code is not None:
        filters.append(HL7v2AuditLog.ack_code == ack_code)
    if message_type is not None:
        filters.append(HL7v2AuditLog.message_type == message_type)
    if sending_application is not None:
        filters.append(HL7v2AuditLog.sending_application == sending_application)
    if sending_facility is not None:
        filters.append(HL7v2AuditLog.sending_facility == sending_facility)
    if start_date is not None:
        filters.append(HL7v2AuditLog.created_at >= start_date)
    if end_date is not None:
        filters.append(HL7v2AuditLog.created_at <= end_date)
    
    # Count total
    count_stmt = select(func.count()).select_from(HL7v2AuditLog)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    
    result = await db.execute(count_stmt)
    total = result.scalar() or 0
    
    # Get paginated results
    stmt = select(HL7v2AuditLog).options(joinedload(HL7v2AuditLog.api_key))
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    # Sort
    sort_column = getattr(HL7v2AuditLog, sort_by, HL7v2AuditLog.created_at)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())
    
    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    # Convert to response
    log_responses = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "api_key_id": log.api_key_id,
            "system_identifier": log.api_key.system_identifier if log.api_key else None,
            "request_ip": log.request_ip,
            "request_user_agent": log.request_user_agent,
            "message_control_id": log.message_control_id,
            "message_type": log.message_type,
            "sending_application": log.sending_application,
            "sending_facility": log.sending_facility,
            "message_size_bytes": log.message_size_bytes,
            "success": log.success,
            "http_status_code": log.http_status_code,
            "ack_code": log.ack_code,
            "error_message": log.error_message,
            "processing_time_ms": log.processing_time_ms,
            "patient_id": log.patient_id,
            "encounter_id": log.encounter_id,
            "created_at": log.created_at,
        }
        log_responses.append(HL7v2AuditLogResponse(**log_dict))
    
    return HL7v2AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        logs=log_responses,
    )


@router.get(
    "/logs/{log_id}",
    response_model=HL7v2AuditLogDetailResponse,
    summary="Get audit log detail",
    description="Get detailed audit log including raw HL7v2 message.",
)
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> HL7v2AuditLogDetailResponse:
    """Get audit log detail by ID."""
    
    stmt = select(HL7v2AuditLog).options(joinedload(HL7v2AuditLog.api_key)).where(HL7v2AuditLog.id == log_id)
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log {log_id} not found",
        )
    
    return HL7v2AuditLogDetailResponse(
        id=log.id,
        api_key_id=log.api_key_id,
        system_identifier=log.api_key.system_identifier if log.api_key else None,
        request_ip=log.request_ip,
        request_user_agent=log.request_user_agent,
        message_control_id=log.message_control_id,
        message_type=log.message_type,
        sending_application=log.sending_application,
        sending_facility=log.sending_facility,
        raw_message=log.raw_message,
        message_size_bytes=log.message_size_bytes,
        success=log.success,
        http_status_code=log.http_status_code,
        ack_code=log.ack_code,
        error_message=log.error_message,
        processing_time_ms=log.processing_time_ms,
        patient_id=log.patient_id,
        encounter_id=log.encounter_id,
        created_at=log.created_at,
    )


@router.get(
    "/stats",
    response_model=HL7v2AuditStatsResponse,
    summary="Get audit statistics",
    description="Get aggregated statistics from audit logs.",
)
async def get_audit_stats(
    db: AsyncSession = Depends(get_db_session),
    api_key_id: Optional[int] = Query(None, description="Filter by API Key ID"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
) -> HL7v2AuditStatsResponse:
    """Get audit statistics."""

    # Build base filter
    filters = []
    if api_key_id is not None:
        filters.append(HL7v2AuditLog.api_key_id == api_key_id)
    if success is not None:
        filters.append(HL7v2AuditLog.success == success)
    if start_date is not None:
        filters.append(HL7v2AuditLog.created_at >= start_date)
    if end_date is not None:
        filters.append(HL7v2AuditLog.created_at <= end_date)

    # Total requests
    stmt = select(func.count()).select_from(HL7v2AuditLog)
    if filters:
        stmt = stmt.where(and_(*filters))
    result = await db.execute(stmt)
    total_requests = result.scalar() or 0

    # Successful requests
    success_filters = filters + [HL7v2AuditLog.success == True]
    stmt = select(func.count()).select_from(HL7v2AuditLog).where(and_(*success_filters))
    result = await db.execute(stmt)
    successful_requests = result.scalar() or 0

    # Failed requests
    failed_requests = total_requests - successful_requests

    # Success rate
    success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0.0

    # Average processing time
    stmt = select(func.avg(HL7v2AuditLog.processing_time_ms)).select_from(HL7v2AuditLog)
    if filters:
        stmt = stmt.where(and_(*filters))
    result = await db.execute(stmt)
    avg_processing_time_ms = result.scalar() or 0.0

    # Total bytes processed
    stmt = select(func.sum(HL7v2AuditLog.message_size_bytes)).select_from(HL7v2AuditLog)
    if filters:
        stmt = stmt.where(and_(*filters))
    result = await db.execute(stmt)
    total_bytes_processed = result.scalar() or 0

    # Unique systems
    stmt = select(func.count(func.distinct(HL7v2AuditLog.api_key_id))).select_from(HL7v2AuditLog)
    if filters:
        stmt = stmt.where(and_(*filters))
    result = await db.execute(stmt)
    unique_systems = result.scalar() or 0

    # By status code
    stmt = select(
        HL7v2AuditLog.http_status_code,
        func.count()
    ).select_from(HL7v2AuditLog).group_by(HL7v2AuditLog.http_status_code)
    if filters:
        stmt = stmt.where(and_(*filters))
    result = await db.execute(stmt)
    by_status_code = {row[0]: row[1] for row in result.all()}

    # By ACK code
    stmt = select(
        HL7v2AuditLog.ack_code,
        func.count()
    ).select_from(HL7v2AuditLog).where(HL7v2AuditLog.ack_code.isnot(None)).group_by(HL7v2AuditLog.ack_code)
    if filters:
        stmt = stmt.where(and_(*filters))
    result = await db.execute(stmt)
    by_ack_code = {row[0]: row[1] for row in result.all()}

    # By message type
    stmt = select(
        HL7v2AuditLog.message_type,
        func.count()
    ).select_from(HL7v2AuditLog).where(HL7v2AuditLog.message_type.isnot(None)).group_by(HL7v2AuditLog.message_type)
    if filters:
        stmt = stmt.where(and_(*filters))
    result = await db.execute(stmt)
    by_message_type = {row[0]: row[1] for row in result.all()}

    return HL7v2AuditStatsResponse(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        success_rate=round(success_rate, 2),
        avg_processing_time_ms=round(avg_processing_time_ms, 2),
        total_bytes_processed=total_bytes_processed,
        unique_systems=unique_systems,
        by_status_code=by_status_code,
        by_ack_code=by_ack_code,
        by_message_type=by_message_type,
    )
