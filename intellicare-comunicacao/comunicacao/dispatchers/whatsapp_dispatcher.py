"""Dispatcher para envio via WhatsApp."""

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


class WhatsAppDispatcher:
    """
    Dispatcher para envio via WhatsApp Business API.
    
    Implementação stub - será completada na Fase 4 (D4 - Notificações Externas).
    """

    channel = "whatsapp"

    def __init__(self, api_key: str = "stub") -> None:
        self.api_key = api_key
        logger.info("WhatsAppDispatcher inicializado (stub)")

    async def send(self, message: ChannelMessage, ctx: Any = None) -> DispatchResult:
        """Envia mensagem via WhatsApp (stub)."""
        logger.info(
            "WhatsAppDispatcher.send (stub): intent=%s, recipient=%s",
            message.intent_id,
            message.recipient.recipient_id,
        )

        # Stub - retorna sucesso simulado
        return DispatchResult(
            success=True,
            channel_message_id=f"whatsapp-{message.intent_id}",
            timestamp=datetime.now(UTC),
        )

    async def get_status(self, channel_message_id: str, ctx: Any = None) -> DeliveryStatus:
        """Consulta status de entrega (stub)."""
        logger.info("WhatsAppDispatcher.get_status (stub): message_id=%s", channel_message_id)
        return DeliveryStatus.SENT

    async def cancel(self, channel_message_id: str, ctx: Any = None) -> bool:
        """Cancela envio pendente (stub)."""
        logger.info("WhatsAppDispatcher.cancel (stub): message_id=%s", channel_message_id)
        return False  # WhatsApp não permite cancelamento após envio

    async def health_check(self, ctx: Any = None) -> ChannelHealth:
        """Verifica saúde do canal (stub)."""
        return ChannelHealth(
            channel=self.channel,
            available=True,
            status="up",
            details={"api": "whatsapp_business", "status": "stub", "latency_ms": 80},
        )

    async def test_send(self, recipient: ResolvedRecipient, ctx: Any = None) -> DispatchResult:
        """Envia mensagem de teste (stub)."""
        logger.info("WhatsAppDispatcher.test_send (stub): recipient=%s", recipient.recipient_id)
        
        return DispatchResult(
            success=True,
            channel_message_id=f"test-whatsapp-{recipient.recipient_id}",
            timestamp=datetime.now(UTC),
        )

    async def get_capabilities(self, ctx: Any = None) -> ChannelCapabilities:
        """Retorna capacidades do canal."""
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=True,
            supports_rich_content=True,
            supports_attachments=True,
            supports_interactive=True,  # Botões, listas, etc
            max_message_length=4096,
            metadata={
                "format": "markdown",
                "api": "whatsapp_business",
                "implementation": "stub",
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient, ctx: Any = None) -> RecipientValidation:
        """Valida destinatário (stub)."""
        phone = recipient.channels.get("whatsapp")
        
        if not phone:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel_address=phone,
                error_message="Telefone WhatsApp não encontrado no destinatário",
            )

        # Validação básica de formato
        if not phone.startswith("+"):
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel_address=phone,
                error_message=f"Telefone deve começar com +: {phone}",
            )

        return RecipientValidation(
            valid=True,
            recipient_id=recipient.recipient_id,
            channel_address=phone,
        )
