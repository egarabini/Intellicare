"""SQLAlchemy ORM models for FHIR Subscriptions in intellicare-grahame."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from grahame.models.base import Base


class Subscription(Base):
    """Persisted FHIR Subscription resource."""

    __tablename__ = "fhir_subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")
    criteria: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    channel_endpoint: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel_header: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    channel_payload: Mapped[str | None] = mapped_column(
        String(128), nullable=True, default="application/fhir+json"
    )
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


class SubscriptionAudit(Base):
    """Audit trail for every subscription notification attempt."""

    __tablename__ = "fhir_subscription_audit"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subscription_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    channel_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )
