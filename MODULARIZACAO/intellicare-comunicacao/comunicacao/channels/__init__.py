"""
Canais externos de comunicação (D4).

Este módulo implementa dispatchers para canais externos:
- Push Notifications (VAPID/FCM)
- WhatsApp Business API
- SMS (Twilio/Zenvia/SNS)
- Email (SMTP)

Cada canal implementa IChannelDispatcher do D1.
"""

from comunicacao.channels.models import (
    ExternalMessageLog,
    ExternalMessageStatus,
    ExternalMessageDirection,
)

__all__ = [
    "ExternalMessageLog",
    "ExternalMessageStatus",
    "ExternalMessageDirection",
]

