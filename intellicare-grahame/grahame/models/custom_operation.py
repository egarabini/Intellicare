"""SQLAlchemy ORM models for custom FHIR operations."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import JSON, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from grahame.models.base import Base


class CustomOperation(Base):
    """Tenant-scoped registry entry for dynamic FHIR operations."""

    __tablename__ = "custom_operations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            "resource_type",
            name="uq_custom_operations_tenant_name_resource",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    op_type: Mapped[str] = mapped_column(String(16), nullable=False)  # instance|system
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    handler_type: Mapped[str] = mapped_column(String(16), nullable=False)  # url|bot|inline
    handler_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


class CustomOperationAudit(Base):
    """Audit row for every custom operation execution attempt."""

    __tablename__ = "custom_operation_audit"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operation_name: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requester: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )
