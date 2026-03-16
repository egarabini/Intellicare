"""Schemas Pydantic para o modulo de notificacoes."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


NotificationType = Literal["appointment", "clinical", "system", "message", "alert"]
NotificationPriority = Literal["low", "normal", "high", "urgent"]


class NotificationCreate(BaseModel):
    """Payload para criar uma notificacao."""

    user_id: str = Field(..., min_length=1, description="ID do usuario destinatario")
    type: NotificationType = "system"
    priority: NotificationPriority = "normal"
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    data: dict[str, Any] = Field(default_factory=dict)


class NotificationBroadcast(BaseModel):
    """Payload para enviar notificacao a todos do tenant."""

    type: NotificationType = "system"
    priority: NotificationPriority = "normal"
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    data: dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    """Resposta com dados de uma notificacao."""

    id: UUID
    user_id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    body: str
    data: dict[str, Any]
    read: bool
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Listagem paginada de notificacoes."""

    items: list[NotificationResponse]
    total: int
    page: int
    size: int


class UnreadCountResponse(BaseModel):
    """Contagem de notificacoes nao lidas."""

    count: int


class NotificationPreferencesResponse(BaseModel):
    """Preferencias de notificacao do usuario."""

    user_id: str
    enabled: bool
    types_enabled: list[NotificationType]
    priority_min: NotificationPriority
    updated_at: datetime | None = None


class NotificationPreferencesUpdate(BaseModel):
    """Payload para atualizar preferencias."""

    enabled: bool | None = None
    types_enabled: list[NotificationType] | None = None
    priority_min: NotificationPriority | None = None
