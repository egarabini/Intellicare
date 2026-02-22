"""Models para Jitsi Meet."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from comunicacao.storage.base import Base


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class RoomType(str, Enum):
    """Tipo de sala Jitsi."""
    
    TELECONSULTA = "teleconsulta"  # Consulta médico-paciente
    MULTIDISCIPLINAR = "multidisciplinar"  # Discussão de caso multidisciplinar
    GRUPO = "grupo"  # Grupo terapêutico
    TREINAMENTO = "treinamento"  # Treinamento de equipe
    EMERGENCIA = "emergencia"  # Atendimento de emergência


class RoomStatus(str, Enum):
    """Status da sala Jitsi."""
    
    SCHEDULED = "scheduled"  # Agendada (futura)
    ACTIVE = "active"  # Em andamento
    COMPLETED = "completed"  # Finalizada
    CANCELLED = "cancelled"  # Cancelada


class ParticipantRole(str, Enum):
    """Papel do participante na sala."""
    
    MODERATOR = "moderator"  # Moderador (pode gravar, expulsar, etc.)
    PRESENTER = "presenter"  # Apresentador (pode compartilhar tela)
    PARTICIPANT = "participant"  # Participante comum


# ═══════════════════════════════════════════════════════════════════════════
# SQLALCHEMY MODELS
# ═══════════════════════════════════════════════════════════════════════════

class JitsiRoom(Base):
    """
    Sala Jitsi Meet.
    
    Representa uma sala de teleconsulta ou reunião multidisciplinar.
    """
    
    __tablename__ = "jitsi_rooms"
    __table_args__ = {"schema": "comunicacao_operacional"}
    
    # Identificação
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    room_name = Column(String(255), nullable=False, unique=True, index=True)
    room_type = Column(SQLEnum(RoomType), nullable=False, index=True)
    status = Column(SQLEnum(RoomStatus), nullable=False, default=RoomStatus.SCHEDULED, index=True)
    
    # Agendamento
    scheduled_start = Column(DateTime(timezone=True), nullable=False, index=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    
    # Configuração
    max_participants = Column(Integer, nullable=False, default=10)
    enable_recording = Column(Boolean, nullable=False, default=True)
    enable_lobby = Column(Boolean, nullable=False, default=True)
    enable_chat = Column(Boolean, nullable=False, default=True)
    enable_screen_sharing = Column(Boolean, nullable=False, default=True)
    moderator_password = Column(String(255), nullable=True)
    
    # Contexto clínico
    patient_id = Column(String(255), nullable=True, index=True)
    intent_id = Column(String(255), nullable=True, index=True)  # Link para CommunicationIntent
    
    # Metadados
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    metadata = Column("extra_metadata", JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    participants = relationship("JitsiParticipant", back_populates="room", cascade="all, delete-orphan")


class JitsiParticipant(Base):
    """
    Participante de sala Jitsi.
    
    Representa um usuário que foi convidado ou participou de uma sala.
    """
    
    __tablename__ = "jitsi_participants"
    __table_args__ = {"schema": "comunicacao_operacional"}
    
    # Identificação
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    room_id = Column(PGUUID(as_uuid=True), ForeignKey("comunicacao_operacional.jitsi_rooms.id"), nullable=False, index=True)
    
    # Usuário
    user_id = Column(String(255), nullable=False, index=True)  # ID do usuário (Keycloak)
    user_name = Column(String(255), nullable=False)
    user_email = Column(String(255), nullable=True)
    role = Column(SQLEnum(ParticipantRole), nullable=False, default=ParticipantRole.PARTICIPANT)
    
    # Participação
    invited_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    left_at = Column(DateTime(timezone=True), nullable=True)
    
    # JWT Token (gerado para acesso)
    jwt_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadados
    metadata = Column("extra_metadata", JSON, nullable=True)
    
    # Relacionamentos
    room = relationship("JitsiRoom", back_populates="participants")


# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════

class JitsiRoomCreate(BaseModel):
    """Request para criar sala Jitsi."""
    
    room_type: RoomType
    scheduled_start: datetime
    scheduled_end: datetime
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    patient_id: str | None = None
    max_participants: int = Field(default=10, ge=2, le=100)
    enable_recording: bool = True
    enable_lobby: bool = True
    enable_chat: bool = True
    enable_screen_sharing: bool = True
    moderator_password: str | None = None
    metadata: dict[str, Any] | None = None


class JitsiParticipantCreate(BaseModel):
    """Request para adicionar participante."""
    
    user_id: str
    user_name: str
    user_email: str | None = None
    role: ParticipantRole = ParticipantRole.PARTICIPANT


class JitsiRoomResponse(BaseModel):
    """Response de sala Jitsi."""
    
    id: UUID
    room_name: str
    room_type: RoomType
    status: RoomStatus
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: datetime | None
    actual_end: datetime | None
    title: str
    description: str | None
    patient_id: str | None
    intent_id: str | None
    room_url: str
    participant_count: int
    
    class Config:
        from_attributes = True

