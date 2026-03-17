"""Contratos e enums da fundacao tecnica do CarePlanner."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Channel(StrEnum):
    ROCKETCHAT = "rocketchat"


class TaskStatus(StrEnum):
    CREATED = "CREATED"
    DISPATCHED = "DISPATCHED"
    SENT = "SENT"
    REPLIED = "REPLIED"
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"

    @classmethod
    def allowed_transitions(cls) -> dict["TaskStatus", set["TaskStatus"]]:
        return {
            cls.CREATED: {cls.DISPATCHED, cls.FAILED, cls.CLOSED},
            cls.DISPATCHED: {cls.SENT, cls.FAILED, cls.EXPIRED, cls.CLOSED},
            cls.SENT: {cls.REPLIED, cls.FAILED, cls.EXPIRED, cls.CLOSED},
            cls.REPLIED: {cls.DISPATCHED, cls.CLOSED, cls.FAILED},
            cls.CLOSED: set(),
            cls.FAILED: set(),
            cls.EXPIRED: set(),
        }

    def can_transition_to(self, next_status: "TaskStatus") -> bool:
        return next_status in self.allowed_transitions()[self]

    def ensure_transition(self, next_status: "TaskStatus") -> None:
        if not self.can_transition_to(next_status):
            raise ValueError(f"Transicao invalida: {self} -> {next_status}")


class EventType(StrEnum):
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_FAILED = "MESSAGE_FAILED"
    INBOUND_RECEIVED = "INBOUND_RECEIVED"
    ORPHAN_INBOUND = "ORPHAN_INBOUND"
    VIDEO_SESSION_OPENED = "VIDEO_SESSION_OPENED"
    TASK_CLOSED = "TASK_CLOSED"


class ParticipantRole(StrEnum):
    PACIENTE = "PACIENTE"
    CLINICO = "CLINICO"


def cast_channel_conversation_id(value: int | str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("channel_conversation_id invalido; esperado BIGINT") from exc


class CareTaskCreate(BaseModel):
    correlation_id: UUID
    kestra_execution_id: str | None = None
    patient_ref: str
    task_type: str
    status: TaskStatus = TaskStatus.CREATED
    channel: Channel = Channel.ROCKETCHAT
    metadata: dict[str, Any] = Field(default_factory=dict)


class CareTaskRecord(CareTaskCreate):
    id: UUID
    tenant_slug: str
    created_at: datetime
    updated_at: datetime


class CareConversationUpsert(BaseModel):
    correlation_id: UUID
    channel: Channel = Channel.ROCKETCHAT
    channel_conversation_id: int | str
    rc_room_id: str | None = None
    phone_e164: str | None = None
    participant_role: ParticipantRole | None = None
    last_interaction_at: datetime | None = None


class CareConversationRecord(BaseModel):
    id: UUID
    correlation_id: UUID
    channel: Channel
    channel_conversation_id: int
    rc_room_id: str | None = None
    phone_e164: str | None = None
    participant_role: str | None = None
    tenant_slug: str
    last_interaction_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CareEventCreate(BaseModel):
    event_id: str
    correlation_id: UUID | None = None
    event_type: EventType
    status: TaskStatus | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class CareEventRecord(BaseModel):
    id: UUID
    event_id: str
    correlation_id: UUID | None = None
    event_type: EventType
    status: str | None = None
    payload: dict[str, Any]
    tenant_slug: str
    created_at: datetime


class CareTemplateCreate(BaseModel):
    template_code: str
    channel: Channel = Channel.ROCKETCHAT
    content: str
    variables: list[str] = Field(default_factory=list)
    active: bool = True


class CareTemplateRecord(BaseModel):
    id: UUID
    template_code: str
    channel: Channel
    content: str
    variables: list[str] = Field(default_factory=list)
    active: bool
    tenant_slug: str
    created_at: datetime
    updated_at: datetime


class CareVideoSessionCreate(BaseModel):
    correlation_id: UUID
    room_name: str
    clinico_jwt: str
    patient_jwt: str
    expires_at: datetime
    clinico_ref: str
    patient_ref: str


class CareVideoSessionRecord(CareVideoSessionCreate):
    id: UUID
    tenant_slug: str
    created_at: datetime
