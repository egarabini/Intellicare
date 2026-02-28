"""
Models para SMS (D4).

Define estruturas de dados para mensagens SMS.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SMSMessage(BaseModel):
    """Mensagem SMS."""

    id: UUID = Field(default_factory=uuid4)
    phone_number: str  # Número do destinatário (+55...)
    text: str  # Texto da mensagem (até 160 caracteres)
    
    # Metadata
    provider: str = "twilio"  # "twilio" | "zenvia" | "sns"
    provider_message_id: Optional[str] = None
    status: str = "pending"  # "pending" | "sent" | "delivered" | "failed"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True


class SMSSendRequest(BaseModel):
    """Request para enviar SMS."""

    to: str  # Número (+55...)
    text: str  # Texto (max 160 caracteres)
    provider: Optional[str] = None  # Provider específico (opcional)

    class Config:
        """Pydantic config."""

        from_attributes = True


class SMSSendResponse(BaseModel):
    """Response ao enviar SMS."""

    message_id: str
    status: str
    to: str
    provider: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class SMSStatusUpdate(BaseModel):
    """Atualização de status de SMS."""

    message_id: str
    status: str  # "sent" | "delivered" | "failed"
    timestamp: datetime
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        """Pydantic config."""

        from_attributes = True

