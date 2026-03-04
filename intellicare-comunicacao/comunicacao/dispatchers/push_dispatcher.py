"""Dispatcher para notificações push."""

from __future__ import annotations

import logging
from typing import Any
from datetime import UTC, datetime

from comunicacao.dispatchers.base import (
    ChannelCapabilities,
    ChannelDispatcher,
    ChannelHealth,
    ChannelMessage,
    DeliveryStatus,
    DispatchResult,
    RecipientValidation,
    ResolvedRecipient,
)

logger = logging.getLogger(__name__)


class PushDispatcher:
    """
    Dispatcher para notificações push (FCM/APNS).
    
    Implementação stub - será completada na Fase 4 (D4 - Notificações Externas).
    """

    channel = "push"

    def __init__(self, provider: str = "fcm") -> None:
        self.provider = provider
        logger.info("PushDispatcher inicializado (stub) - provider=%s", provider)

    async def send(self, message: ChannelMessage, ctx: Any = None) -> DispatchResult:
        """Envia notificação push (stub)."""
        logger.info(
            "PushDispatcher.send (stub): intent=%s, recipient=%s",
            message.intent_id,
            message.recipient.recipient_id,
        )

        # Stub - retorna sucesso simulado
        return DispatchResult(
            success=True,
            channel_message_id=f"push-{message.intent_id}",
            timestamp=datetime.now(UTC),
        )

    async def get_status(self, channel_message_id: str, ctx: Any = None) -> DeliveryStatus:
        """Consulta status de entrega (stub)."""
        logger.info("PushDispatcher.get_status (stub): message_id=%s", channel_message_id)
        return DeliveryStatus.SENT

    async def cancel(self, channel_message_id: str, ctx: Any = None) -> bool:
        """Cancela envio pendente (stub)."""
        logger.info("PushDispatcher.cancel (stub): message_id=%s", channel_message_id)
        return False  # Push não pode ser cancelado após envio

    async def health_check(self, ctx: Any = None) -> ChannelHealth:
        """Verifica saúde do canal (stub)."""
        return ChannelHealth(
            channel=self.channel,
            available=True,
            status="up",
            details={"provider": self.provider, "status": "stub", "latency_ms": 60},
        )

    async def test_send(self, recipient: ResolvedRecipient, ctx: Any = None) -> DispatchResult:
        """Envia mensagem de teste (stub)."""
        logger.info("PushDispatcher.test_send (stub): recipient=%s", recipient.recipient_id)
        
        return DispatchResult(
            success=True,
            channel_message_id=f"test-push-{recipient.recipient_id}",
            timestamp=datetime.now(UTC),
        )

    async def get_capabilities(self, ctx: Any = None) -> ChannelCapabilities:
        """Retorna capacidades do canal."""
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=False,
            supports_rich_content=True,
            supports_attachments=False,
            supports_interactive=True,  # Ações/botões
            max_message_length=256,  # Limite típico de notificações
            metadata={
                "format": "json",
                "provider": self.provider,
                "implementation": "stub",
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient, ctx: Any = None) -> RecipientValidation:
        """Valida destinatário (stub)."""
        device_token = recipient.channels.get("push")
        
        if not device_token:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel_address=device_token,
                error_message="Device token não encontrado no destinatário",
            )

        # Validação básica de formato
        if len(device_token) < 32:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel_address=device_token,
                error_message=f"Device token inválido (muito curto): {device_token}",
            )

        return RecipientValidation(
            valid=True,
            recipient_id=recipient.recipient_id,
            channel_address=device_token,
        )
