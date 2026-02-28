"""Modelos de auditoria."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from comunicacao.database import Base


class AuditEntry(Base):
    """
    Entrada de auditoria (IMUTÁVEL - APPEND-ONLY).
    
    Cada comunicação gera uma entrada de audit com hash chain
    para garantir integridade (semelhante a blockchain simplificado).
    """
    
    __tablename__ = "audit_trail"
    __table_args__ = {"schema": "comunicacao_operacional"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Comunicação
    intent_id = Column(String(200), nullable=True, index=True)
    delivery_id = Column(String(200), nullable=True)
    
    # O quê
    intent_type = Column(String(50), nullable=False)
    template_name = Column(String(200), nullable=True)
    channel = Column(String(20), nullable=False)
    
    # Para quem (pseudonimizado)
    recipient_type = Column(String(50), nullable=False)
    recipient_hash = Column(String(64), nullable=True)  # SHA-256 hash
    patient_hash = Column(String(64), nullable=True)    # SHA-256 hash
    
    # Resultado
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    
    # LGPD
    legal_basis = Column(String(50), nullable=True)
    lgpd_override = Column(Boolean, nullable=False, default=False)
    lgpd_reason = Column(Text, nullable=True)
    consent_status = Column(String(20), nullable=True)
    
    # Severidade
    severity = Column(String(20), nullable=False)
    
    # Fonte
    source_module = Column(String(50), nullable=True)
    source_event_id = Column(String(200), nullable=True)
    
    # Hash chain (integridade)
    previous_hash = Column(String(64), nullable=True)  # Hash do entry anterior
    entry_hash = Column(String(64), nullable=False, unique=True)  # Hash deste entry
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Metadados
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    # FHIR Communication (se aplicável)
    fhir_communication_id = Column(String(200), nullable=True)
    fhir_communication_json = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AuditEntry(id={self.id}, intent_id={self.intent_id}, channel={self.channel}, status={self.status})>"

