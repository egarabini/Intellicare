"""Modelos de dados para conformidade LGPD."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from comunicacao.database import Base


# ── Enums ──


class LegalBasis(str, Enum):
    """Base legal para processamento de dados (Art. 7º LGPD)."""
    
    CONSENT = "consent"                      # Art. 7º, I - Consentimento
    VITAL_PROTECTION = "vital_protection"    # Art. 7º, VII + Art. 11, II, f - Proteção da vida
    HEALTH_PROTECTION = "health_protection"  # Art. 7º, VII - Tutela da saúde
    LEGAL_OBLIGATION = "legal_obligation"    # Art. 7º, II - Obrigação legal
    PUBLIC_INTEREST = "public_interest"      # Art. 7º, VIII - Interesse público (SUS)


class ConsentStatus(str, Enum):
    """Status de consentimento do paciente."""
    
    GRANTED = "granted"          # Consentimento concedido
    DENIED = "denied"            # Consentimento negado
    WITHDRAWN = "withdrawn"      # Consentimento revogado
    EXPIRED = "expired"          # Consentimento expirado
    PENDING = "pending"          # Aguardando consentimento


# ── Pydantic Models (DTOs) ──


class LGPDDecision(BaseModel):
    """
    Decisão de conformidade LGPD para uma comunicação.
    
    Retornado por LGPDComplianceService.check_compliance().
    """
    
    allowed: bool = Field(
        description="Se a comunicação é permitida"
    )
    
    reason: str = Field(
        description="Razão da decisão (ex: 'Consentimento concedido', 'Bloqueado por quiet hours')"
    )
    
    legal_basis: Optional[LegalBasis] = Field(
        default=None,
        description="Base legal para processamento (se aplicável)"
    )
    
    override_applied: bool = Field(
        default=False,
        description="Se foi aplicado override para alerta CRITICAL/HIGH"
    )
    
    deferred_until: Optional[datetime] = Field(
        default=None,
        description="Se bloqueado por quiet hours, quando pode ser enviado"
    )


class QuietHours(BaseModel):
    """Horários silenciosos (não perturbar)."""
    
    start: str = Field(
        description="Horário de início (HH:MM)",
        pattern=r"^\d{2}:\d{2}$"
    )
    
    end: str = Field(
        description="Horário de fim (HH:MM)",
        pattern=r"^\d{2}:\d{2}$"
    )


# ── SQLAlchemy Models (Database) ──


class CommunicationPreference(Base):
    """
    Preferências de comunicação do paciente.
    
    Armazena opt-in/opt-out por canal e quiet hours.
    """
    
    __tablename__ = "communication_preferences"
    __table_args__ = {"schema": "comunicacao_operacional"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Paciente
    patient_id = Column(String(200), nullable=False, unique=True, index=True)
    
    # Canais habilitados (opt-in)
    rocketchat_enabled = Column(Boolean, nullable=False, default=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    sms_enabled = Column(Boolean, nullable=False, default=True)
    whatsapp_enabled = Column(Boolean, nullable=False, default=True)
    push_enabled = Column(Boolean, nullable=False, default=True)
    jitsi_enabled = Column(Boolean, nullable=False, default=True)
    
    # Quiet hours (JSON: {"start": "22:00", "end": "07:00"})
    quiet_hours = Column(JSON, nullable=True)
    
    # Consentimento
    consent_given = Column(Boolean, nullable=False, default=False)
    consent_given_at = Column(DateTime(timezone=True), nullable=True)
    consent_version = Column(String(20), nullable=True)
    consent_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadados
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<CommunicationPreference(patient_id={self.patient_id}, consent={self.consent_given})>"


class ConsentLogEntry(Base):
    """
    Log de consentimento do paciente.
    
    Trilha imutável de todas as mudanças de consentimento (APPEND-ONLY).
    """
    
    __tablename__ = "consent_log"
    __table_args__ = {"schema": "comunicacao_operacional"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Paciente
    patient_id = Column(String(200), nullable=False, index=True)
    
    # Consentimento
    consent_status = Column(String(20), nullable=False)  # ConsentStatus enum
    consent_version = Column(String(20), nullable=False)
    
    # Timestamp
    consent_given_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Metadados
    extra_metadata = Column("metadata", JSON, nullable=True)  # IP, user agent, etc.
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<ConsentLogEntry(patient_id={self.patient_id}, status={self.consent_status})>"

