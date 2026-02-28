"""Pydantic models for the Bots Engine — no SQLAlchemy in core."""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    """Metadata about the FHIR event that triggered the bot."""

    subscription_id: Optional[str] = None
    interaction: Literal["create", "update", "delete", "execute"] = "create"
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    tenant_id: str = "default"
    triggered_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class BotRecord(BaseModel):
    """Lightweight bot descriptor passed from DB to the execution engine."""

    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    code: str
    runtime: Literal["sandbox", "subprocess"] = "sandbox"
    status: Literal["active", "inactive"] = "active"
    run_as_user: bool = False
    timeout_seconds: int = 30
    code_version: int = 1
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    model_config = {"from_attributes": True}


class BotSecretRecord(BaseModel):
    """Decrypted secret value (never serialised to DB in plaintext)."""

    id: str
    tenant_id: str
    bot_id: Optional[str] = None
    name: str
    value: str  # decrypted plaintext


class BotExecutionResult(BaseModel):
    """Result of a single bot execution."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bot_id: str
    tenant_id: str
    subscription_id: Optional[str] = None
    interaction: str = "create"
    input_resource_type: Optional[str] = None
    input_resource_id: Optional[str] = None
    success: bool
    log_output: str = ""
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class BotExecutionRequest(BaseModel):
    """Request to execute a bot (for $execute endpoint)."""

    input_resource: dict[str, Any]
    interaction: str = "execute"
    secrets_override: Optional[dict[str, str]] = None
