"""Pydantic models for FHIR Subscriptions — pure data, no SQLAlchemy in core."""

from __future__ import annotations

import datetime
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SubscriptionRecord(BaseModel):
    """Lightweight subscription record passed from DB layer to core engine."""

    id: str
    tenant_id: str
    status: Literal["requested", "active", "off", "error"]
    criteria: str
    channel_type: Literal["rest-hook", "websocket", "bot"]
    channel_endpoint: Optional[str] = None
    channel_header: Optional[dict] = None
    error_count: int = 0
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    model_config = {"from_attributes": True}


class ChannelResult(BaseModel):
    """Result of dispatching to a channel."""

    subscription_id: str
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class AuditRecord(BaseModel):
    """Structured audit record for one notification attempt."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subscription_id: str
    tenant_id: str
    event_type: Literal["matched", "dispatched", "failed", "deactivated"]
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    channel_type: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    details: dict = Field(default_factory=dict)
