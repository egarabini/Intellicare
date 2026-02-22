"""Dispatchers de canais de comunicacao."""

from comunicacao.dispatchers.base import (
    ChannelDispatcher,
    ChannelHealth,
    ChannelMessage,
    DeliveryStatus,
    DispatchResult,
    DispatcherManager,
    RenderedContent,
    ResolvedRecipient,
    create_default_dispatcher_manager,
)
from comunicacao.dispatchers.email_dispatcher import EmailDispatcher
from comunicacao.dispatchers.push_dispatcher import PushDispatcher
from comunicacao.dispatchers.rocketchat_dispatcher import RocketChatDispatcher
from comunicacao.dispatchers.sms_dispatcher import SMSDispatcher
from comunicacao.dispatchers.whatsapp_dispatcher import WhatsAppDispatcher

__all__ = [
    "ChannelDispatcher",
    "ChannelHealth",
    "ChannelMessage",
    "DeliveryStatus",
    "DispatchResult",
    "DispatcherManager",
    "RenderedContent",
    "ResolvedRecipient",
    "create_default_dispatcher_manager",
    "RocketChatDispatcher",
    "EmailDispatcher",
    "SMSDispatcher",
    "PushDispatcher",
    "WhatsAppDispatcher",
]
