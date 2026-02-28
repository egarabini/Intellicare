"""
Models para Push Notifications (D4).

Define estruturas de dados para VAPID e FCM.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PushPayload(BaseModel):
    """Payload enviado na push notification."""

    title: str  # Título da notificação
    body: str  # Corpo da mensagem
    icon: str = "/icons/intellicare-192.png"
    badge: str = "/icons/badge-72.png"
    tag: Optional[str] = None  # Agrupa notificações (ex: "alert-P001")
    data: Optional[Dict] = None  # Dados extras para o Service Worker
    actions: Optional[List[Dict]] = None  # Botões de ação
    # Exemplo de actions:
    # [
    #   { "action": "view", "title": "Ver Detalhes", "icon": "/icons/view.png" },
    #   { "action": "dismiss", "title": "Dispensar" }
    # ]
    require_interaction: bool = False  # True para alertas CRITICAL
    renotify: bool = True  # Vibrar novamente mesmo com mesmo tag
    silent: bool = False  # Sem som (para LOW severity)

    class Config:
        """Pydantic config."""

        from_attributes = True


class PushSubscriptionRequest(BaseModel):
    """Request para registrar subscription de push."""

    subscription_type: str  # "web" | "fcm"

    # Web Push (VAPID)
    endpoint: Optional[str] = None
    p256dh_key: Optional[str] = None
    auth_key: Optional[str] = None

    # FCM
    fcm_token: Optional[str] = None

    # Metadata
    device_name: Optional[str] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class PushSubscriptionResponse(BaseModel):
    """Response ao registrar subscription."""

    subscription_id: str
    user_id: str
    subscription_type: str
    device_name: Optional[str] = None
    created_at: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class PushTestRequest(BaseModel):
    """Request para enviar push de teste."""

    title: str = "Teste IntelliCare"
    body: str = "Esta é uma notificação de teste do sistema IntelliCare."
    require_interaction: bool = False

    class Config:
        """Pydantic config."""

        from_attributes = True


class PushTestResponse(BaseModel):
    """Response ao enviar push de teste."""

    sent_to: int
    failed: int
    details: List[Dict]

    class Config:
        """Pydantic config."""

        from_attributes = True


class VAPIDPublicKeyResponse(BaseModel):
    """Response com VAPID public key."""

    public_key: str

    class Config:
        """Pydantic config."""

        from_attributes = True

