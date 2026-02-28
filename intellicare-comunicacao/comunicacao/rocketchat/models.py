"""Modelos de dados para Rocket.Chat."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RCUser(BaseModel):
    """Usuário do Rocket.Chat."""
    
    id: str = Field(..., description="ID do usuário no RC (_id)")
    username: str = Field(..., description="Username único")
    name: str | None = Field(None, description="Nome completo")
    email: str | None = Field(None, description="Email")
    status: str = Field("offline", description="Status: online, away, busy, offline")
    active: bool = Field(True, description="Conta ativa?")
    roles: list[str] = Field(default_factory=list, description="Roles no RC")
    created_at: datetime | None = Field(None, description="Data de criação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "username": "joao.silva",
                "name": "João Silva",
                "email": "joao.silva@example.com",
                "status": "online",
                "active": True,
                "roles": ["user", "doctor"],
            }
        }


class RCChannel(BaseModel):
    """Canal/Room do Rocket.Chat."""
    
    id: str = Field(..., description="ID do canal (_id)")
    name: str = Field(..., description="Nome do canal (sem #)")
    type: str = Field(..., description="Tipo: c (channel), p (private group), d (direct)")
    topic: str | None = Field(None, description="Tópico do canal")
    description: str | None = Field(None, description="Descrição")
    announcement: str | None = Field(None, description="Anúncio fixo")
    members_count: int = Field(0, description="Número de membros")
    read_only: bool = Field(False, description="Somente leitura?")
    archived: bool = Field(False, description="Arquivado?")
    created_at: datetime | None = Field(None, description="Data de criação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "xyz789",
                "name": "caso-patient-123",
                "type": "p",
                "topic": "Caso clínico - Paciente Maria Santos",
                "members_count": 5,
                "read_only": False,
                "archived": False,
            }
        }


class RCAttachment(BaseModel):
    """Attachment de mensagem do Rocket.Chat."""
    
    title: str | None = Field(None, description="Título do attachment")
    title_link: str | None = Field(None, description="Link do título")
    text: str | None = Field(None, description="Texto do attachment")
    color: str | None = Field(None, description="Cor da barra lateral (hex)")
    image_url: str | None = Field(None, description="URL da imagem")
    thumb_url: str | None = Field(None, description="URL do thumbnail")
    author_name: str | None = Field(None, description="Nome do autor")
    author_icon: str | None = Field(None, description="Ícone do autor")
    fields: list[dict[str, Any]] = Field(default_factory=list, description="Campos estruturados")
    actions: list[dict[str, Any]] = Field(default_factory=list, description="Botões/ações")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Alerta Crítico",
                "text": "eGFR caiu para 25 ml/min",
                "color": "#FF0000",
                "fields": [
                    {"title": "Paciente", "value": "Maria Santos", "short": True},
                    {"title": "Severidade", "value": "CRITICAL", "short": True},
                ],
            }
        }


class RCMessage(BaseModel):
    """Mensagem do Rocket.Chat."""
    
    id: str | None = Field(None, description="ID da mensagem (_id)")
    room_id: str = Field(..., description="ID do canal/room")
    text: str = Field(..., description="Texto da mensagem (Markdown)")
    alias: str | None = Field(None, description="Nome do remetente (override)")
    emoji: str | None = Field(None, description="Emoji avatar (ex: :robot:)")
    avatar: str | None = Field(None, description="URL do avatar")
    attachments: list[RCAttachment] = Field(default_factory=list, description="Attachments")
    user_id: str | None = Field(None, description="ID do usuário remetente")
    username: str | None = Field(None, description="Username do remetente")
    timestamp: datetime | None = Field(None, description="Timestamp da mensagem")
    
    class Config:
        json_schema_extra = {
            "example": {
                "room_id": "xyz789",
                "text": "**Alerta Crítico**: eGFR caiu para 25 ml/min",
                "alias": "IntelliCare Bot",
                "emoji": ":robot:",
                "attachments": [],
            }
        }


class RCMessageResponse(BaseModel):
    """Resposta de envio de mensagem."""
    
    message_id: str = Field(..., description="ID da mensagem criada")
    channel_id: str = Field(..., description="ID do canal")
    timestamp: str = Field(..., description="Timestamp ISO")
    success: bool = Field(True, description="Sucesso?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg123",
                "channel_id": "xyz789",
                "timestamp": "2026-02-17T10:30:00Z",
                "success": True,
            }
        }

    @property
    def id(self) -> str:
        """Alias legado para message_id."""
        return self.message_id

    @property
    def room_id(self) -> str:
        """Alias legado para channel_id."""
        return self.channel_id


class RCChannelCreateRequest(BaseModel):
    """Request para criar canal."""
    
    name: str = Field(..., description="Nome do canal (sem #)")
    type: str = Field("p", description="Tipo: c (público) ou p (privado)")
    members: list[str] = Field(default_factory=list, description="Usernames dos membros iniciais")
    topic: str | None = Field(None, description="Tópico do canal")
    description: str | None = Field(None, description="Descrição")
    read_only: bool = Field(False, description="Somente leitura?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "caso-patient-456",
                "type": "p",
                "members": ["joao.silva", "maria.santos"],
                "topic": "Caso clínico - Paciente João Silva",
                "read_only": False,
            }
        }
