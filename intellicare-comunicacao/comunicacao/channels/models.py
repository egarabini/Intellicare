"""
Models compartilhados para canais externos (D4).

Define modelos de dados para log unificado de mensagens externas.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExternalMessageStatus(str, Enum):
    """Status de mensagem externa."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class ExternalMessageDirection(str, Enum):
    """Direção da mensagem."""

    OUTBOUND = "outbound"
    INBOUND = "inbound"


class ExternalMessageLog(BaseModel):
    """
    Log unificado de mensagens de canais externos.

    Armazena histórico de todas as mensagens enviadas/recebidas
    via Push, WhatsApp, SMS e Email.
    """

    id: UUID = Field(default_factory=uuid4)
    channel: str  # "push" | "whatsapp" | "sms" | "email"
    direction: ExternalMessageDirection

    # Destinatário
    recipient_id: Optional[str] = None  # user_id ou patient_id
    recipient_address: Optional[str] = None  # phone, email, etc.

    # Conteúdo
    template_name: Optional[str] = None
    message_summary: Optional[str] = None  # Truncado para log (sem PII detalhado)

    # Provider
    provider_message_id: Optional[str] = None  # ID do provider (Twilio SID, Meta msg ID, etc.)
    provider_status: Optional[str] = None  # Status do provider

    # Status IntelliCare
    status: ExternalMessageStatus = ExternalMessageStatus.PENDING
    error_message: Optional[str] = None

    # Rastreamento
    delivery_result_id: Optional[UUID] = None  # FK para delivery_results (D1)

    # Timestamps
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class PushSubscription(BaseModel):
    """Subscription de push notification de um dispositivo."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str  # Keycloak user_id
    subscription_type: str  # "web" | "fcm"

    # Web Push (VAPID)
    endpoint: Optional[str] = None  # URL do push service
    p256dh_key: Optional[str] = None  # Chave pública do cliente
    auth_key: Optional[str] = None  # Auth secret do cliente

    # FCM
    fcm_token: Optional[str] = None  # Token do dispositivo Firebase

    # Metadata
    device_name: Optional[str] = None  # "Chrome Desktop", "Android App"
    user_agent: Optional[str] = None
    active: bool = True
    last_used_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True


class WhatsAppSession(BaseModel):
    """Sessão WhatsApp (janela de 24h)."""

    id: UUID = Field(default_factory=uuid4)
    phone_number: str
    patient_id: Optional[str] = None

    # Janela de sessão
    session_started_at: datetime  # Quando paciente enviou última msg
    session_expires_at: datetime  # +24h
    active: bool = True

    # Contadores
    messages_sent: int = 0
    messages_received: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True


class ChannelConfig(BaseModel):
    """Configuração de canal por tenant/unidade."""

    id: UUID = Field(default_factory=uuid4)
    channel: str  # "push" | "whatsapp" | "sms" | "email"
    config_key: str
    config_value: str
    encrypted: bool = False  # Se valor está criptografado

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True

