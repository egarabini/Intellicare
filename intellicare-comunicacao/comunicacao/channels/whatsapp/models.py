"""
Models para WhatsApp Business API (D4).

Define estruturas de dados para mensagens WhatsApp.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WhatsAppMessage(BaseModel):
    """Mensagem WhatsApp."""

    id: UUID = Field(default_factory=uuid4)
    phone_number: str  # Número do destinatário (+55...)
    template_name: Optional[str] = None
    template_params: Optional[List[str]] = None
    text: Optional[str] = None  # Para session messages
    message_type: str = "template"  # "template" | "text" | "interactive"
    
    # Metadata
    provider_message_id: Optional[str] = None
    status: str = "pending"  # "pending" | "sent" | "delivered" | "read" | "failed"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True


class WhatsAppSendRequest(BaseModel):
    """Request para enviar mensagem WhatsApp."""

    to: str  # Número (+55...)
    template_name: str
    template_params: List[str]
    language: str = "pt_BR"

    class Config:
        """Pydantic config."""

        from_attributes = True


class WhatsAppSendResponse(BaseModel):
    """Response ao enviar mensagem WhatsApp."""

    message_id: str
    status: str
    to: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class WhatsAppTemplateInfo(BaseModel):
    """Informações de um template WhatsApp."""

    name: str
    status: str  # "APPROVED" | "PENDING" | "REJECTED"
    language: str
    category: str  # "UTILITY" | "MARKETING" | "AUTHENTICATION"
    components: List[Dict]

    class Config:
        """Pydantic config."""

        from_attributes = True


class WhatsAppWebhookEvent(BaseModel):
    """Evento recebido via webhook."""

    object: str  # "whatsapp_business_account"
    entry: List[Dict]

    class Config:
        """Pydantic config."""

        from_attributes = True


class WhatsAppStatusUpdate(BaseModel):
    """Atualização de status de mensagem."""

    message_id: str
    status: str  # "sent" | "delivered" | "read" | "failed"
    timestamp: datetime
    recipient_id: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class WhatsAppIncomingMessage(BaseModel):
    """Mensagem recebida do paciente."""

    message_id: str
    from_number: str
    timestamp: datetime
    message_type: str  # "text" | "button" | "interactive"
    text: Optional[str] = None
    button_payload: Optional[str] = None
    interactive_reply: Optional[Dict] = None

    class Config:
        """Pydantic config."""

        from_attributes = True

