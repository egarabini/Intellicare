"""Modelos de dominio do roteamento."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RecipientType(str, Enum):
    PROFESSIONAL = "professional"
    PATIENT = "patient"
    TEAM = "team"
    COORDINATOR = "coordinator"
    BROADCAST = "broadcast"


class IntentStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class ChannelStep(BaseModel):
    channel: str
    timeout_seconds: int | None = None
    concurrent: bool = False
    delay_seconds: int = 0


class RoutingRule(BaseModel):
    id: str
    name: str
    priority: int = 100
    active: bool = True
    severities: list[str] = Field(default_factory=list)
    recipient_types: list[RecipientType] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    channels: list[ChannelStep] = Field(default_factory=list)


class CommunicationIntentCreate(BaseModel):
    """Schema para criação de nova intenção de comunicação."""

    source_module: str = Field(min_length=1, max_length=120)
    source_event_id: str | None = Field(default=None, max_length=200)
    recipient_type: RecipientType
    recipient_id: str = Field(min_length=1, max_length=200)
    severity: str = Field(min_length=1, max_length=20)
    category: str = Field(min_length=1, max_length=60)

    # Conteúdo (template OU raw, não ambos)
    content_template_id: str | None = Field(default=None, max_length=100)
    content_params: dict[str, Any] | None = Field(default=None)
    content_raw: str | None = Field(default=None, max_length=4000)

    # Controle de entrega
    correlation_id: str = Field(min_length=1, max_length=200)
    preferred_channel: str | None = Field(default=None, max_length=30)
    excluded_channels: list[str] = Field(default_factory=list)
    require_ack: bool = False
    max_attempts: int = Field(default=3, ge=1, le=10)

    # Agendamento
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None

    # Escalonamento
    parent_intent_id: UUID | None = None

    # Metadados
    metadata: dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: str
    channel: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class DeliveryResultRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    channel: str
    attempt_number: int = 1
    status: DeliveryStatus
    channel_message_id: str | None = None
    channel_room_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CommunicationIntentRecord(BaseModel):
    """Registro completo de intenção de comunicação (persistido)."""

    id: UUID = Field(default_factory=uuid4)
    source_module: str
    source_event_id: str | None = None
    recipient_type: RecipientType
    recipient_id: str
    severity: str
    category: str

    # Conteúdo
    content_template_id: str | None = None
    content_params: dict[str, Any] | None = None
    content_raw: str | None = None

    # Controle de entrega
    correlation_id: str
    preferred_channel: str | None = None
    excluded_channels: list[str] = Field(default_factory=list)
    require_ack: bool = False
    max_attempts: int = 3

    # Agendamento
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None

    # Escalonamento
    parent_intent_id: UUID | None = None

    # Metadados
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Controle interno
    status: IntentStatus = IntentStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    timeline: list[TimelineEvent] = Field(default_factory=list)
