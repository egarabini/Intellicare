"""
Push Notifications (VAPID/FCM) - D4.

Implementa dispatcher para notificações push via:
- Web Push (VAPID - RFC 8292)
- Firebase Cloud Messaging (FCM)
"""

from comunicacao.channels.push.config import PushConfig, VAPIDConfig, FCMConfig
from comunicacao.channels.push.dispatcher import PushDispatcher
from comunicacao.channels.push.fcm_service import FCMPushService
from comunicacao.channels.push.models import (
    PushPayload,
    PushSubscriptionRequest,
    PushSubscriptionResponse,
    PushTestRequest,
    PushTestResponse,
    VAPIDPublicKeyResponse,
)
from comunicacao.channels.push.vapid_service import VAPIDPushService

__all__ = [
    "PushConfig",
    "VAPIDConfig",
    "FCMConfig",
    "PushDispatcher",
    "VAPIDPushService",
    "FCMPushService",
    "PushPayload",
    "PushSubscriptionRequest",
    "PushSubscriptionResponse",
    "PushTestRequest",
    "PushTestResponse",
    "VAPIDPublicKeyResponse",
]

