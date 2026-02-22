"""Módulo de integração com Rocket.Chat v7.13.2."""

from __future__ import annotations

from comunicacao.rocketchat.channel_service import (
    ChannelType,
    RocketChatChannelService,
)
from comunicacao.rocketchat.client import RocketChatClient
from comunicacao.rocketchat.config import RocketChatConfig
from comunicacao.rocketchat.dispatcher import RocketChatDispatcher
from comunicacao.rocketchat.models import (
    RCAttachment,
    RCChannel,
    RCMessage,
    RCUser,
)
from comunicacao.rocketchat.webhook_handler import (
    RCWebhookMessage,
    RocketChatWebhookHandler,
    WebhookValidationError,
)

__all__ = [
    "RocketChatClient",
    "RocketChatConfig",
    "RocketChatDispatcher",
    "RocketChatChannelService",
    "ChannelType",
    "RCMessage",
    "RCChannel",
    "RCUser",
    "RCAttachment",
    "RocketChatWebhookHandler",
    "RCWebhookMessage",
    "WebhookValidationError",
]

