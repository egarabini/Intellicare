"""HL7v2 Audit Log Model — Auditoria completa de mensagens HL7v2.

Este modelo registra TODAS as requisições HL7v2 recebidas, incluindo:
- Mensagem completa (raw)
- API Key usada
- IP de origem
- Resultado do processamento
- Tempo de processamento

Compliance: LGPD, HIPAA, ISO 27001
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grahame.models.base import Base


class HL7v2AuditLog(Base):
    """Audit log para mensagens HL7v2.
    
    Registra todas as requisições HL7v2 para auditoria e compliance.
    """
    
    __tablename__ = "hl7v2_audit_logs"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # API Key usada
    api_key_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("hl7v2_api_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="API Key usada (NULL se autenticação falhou)"
    )
    
    # Informações da requisição
    request_ip: Mapped[str] = mapped_column(
        String(45),  # IPv6 max length
        nullable=False,
        index=True,
        comment="IP de origem da requisição"
    )
    
    request_user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="User-Agent do cliente"
    )
    
    # Mensagem HL7v2
    message_control_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="MSH-10 (Message Control ID)"
    )
    
    message_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="MSH-9 (Message Type, ex: ADT^A04)"
    )
    
    sending_application: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="MSH-3 (Sending Application)"
    )
    
    sending_facility: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="MSH-4 (Sending Facility)"
    )
    
    # Mensagem completa (raw)
    raw_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Mensagem HL7v2 completa (raw)"
    )
    
    message_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Tamanho da mensagem em bytes"
    )
    
    # Resultado do processamento
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
        comment="True se processamento foi bem-sucedido"
    )
    
    http_status_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="HTTP status code da resposta"
    )
    
    ack_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="ACK code (AA, AR, AE)"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mensagem de erro (se houver)"
    )
    
    # Performance
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Tempo de processamento em milissegundos"
    )
    
    # FHIR Resources criados
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID do Patient FHIR criado"
    )
    
    encounter_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID do Encounter FHIR criado"
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        comment="Data/hora da requisição"
    )
    
    # Relationship (opcional)
    api_key: Mapped[Optional["HL7v2APIKey"]] = relationship(
        "HL7v2APIKey",
        back_populates="audit_logs",
    )
