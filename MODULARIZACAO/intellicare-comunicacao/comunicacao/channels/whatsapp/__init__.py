"""
WhatsApp Business API - D4.

Implementa dispatcher para WhatsApp via Meta Cloud API (Graph API v18.0).
Suporta:
- Template Messages (pré-aprovados)
- Session Messages (janela 24h)
- Interactive Messages (botões, listas)
"""

from comunicacao.channels.whatsapp.client import WhatsAppClient
from comunicacao.channels.whatsapp.config import WhatsAppConfig
from comunicacao.channels.whatsapp.dispatcher import WhatsAppDispatcher
from comunicacao.channels.whatsapp.models import (
    WhatsAppIncomingMessage,
    WhatsAppMessage,
    WhatsAppSendRequest,
    WhatsAppSendResponse,
    WhatsAppStatusUpdate,
    WhatsAppTemplateInfo,
    WhatsAppWebhookEvent,
)
from comunicacao.channels.whatsapp.templates import get_template, list_templates
from comunicacao.channels.whatsapp.webhook_handler import WhatsAppWebhookHandler

__all__ = [
    "WhatsAppConfig",
    "WhatsAppClient",
    "WhatsAppDispatcher",
    "WhatsAppWebhookHandler",
    "WhatsAppMessage",
    "WhatsAppSendRequest",
    "WhatsAppSendResponse",
    "WhatsAppTemplateInfo",
    "WhatsAppWebhookEvent",
    "WhatsAppStatusUpdate",
    "WhatsAppIncomingMessage",
    "get_template",
    "list_templates",
]

