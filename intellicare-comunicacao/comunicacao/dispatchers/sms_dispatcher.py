"""Dispatcher para envio de SMS."""

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


class SMSDispatcher:
    """
    Dispatcher para envio de SMS.
    
    Implementação stub - será completada na Fase 4 (D4 - Notificações Externas).
    """

    channel = "sms"

    def __init__(self, provider: str = "twilio") -> None:
        self.provider = provider
        logger.info("SMSDispatcher inicializado (stub) - provider=%s", provider)

    def _get_provider(self, ctx: Any = None) -> str:
        if ctx and hasattr(ctx, "tenant_settings") and isinstance(ctx.tenant_settings, dict):
            return ctx.tenant_settings.get("sms_provider", self.provider)
        return self.provider

    async def send(self, message: ChannelMessage, ctx: Any = None) -> DispatchResult:
        """Envia SMS (stub)."""
        logger.info(
            "SMSDispatcher.send (stub): intent=%s, recipient=%s",
            message.intent_id,
            message.recipient.recipient_id,
        )

        # Stub - retorna sucesso simulado
        return DispatchResult(
            success=True,
            channel_message_id=f"sms-{message.intent_id}",
            timestamp=datetime.now(UTC),
        )

    async def get_status(self, channel_message_id: str, ctx: Any = None) -> DeliveryStatus:
        """Consulta status de entrega (stub)."""
        logger.info("SMSDispatcher.get_status (stub): message_id=%s", channel_message_id)
        return DeliveryStatus.SENT

    async def cancel(self, channel_message_id: str, ctx: Any = None) -> bool:
        """Cancela envio pendente (stub)."""
        logger.info("SMSDispatcher.cancel (stub): message_id=%s", channel_message_id)
        return False  # SMS não podem ser cancelados após envio

    async def health_check(self, ctx: Any = None) -> ChannelHealth:
        """Verifica saúde do canal (stub)."""
        provider = self._get_provider(ctx)
        return ChannelHealth(
            channel=self.channel,
            available=True,
            status="up",
            details={"provider": provider, "status": "stub", "latency_ms": 100},
        )

    async def test_send(self, recipient: ResolvedRecipient, ctx: Any = None) -> DispatchResult:
        """Envia mensagem de teste (stub)."""
        logger.info("SMSDispatcher.test_send (stub): recipient=%s", recipient.recipient_id)
        
        return DispatchResult(
            success=True,
            channel_message_id=f"test-sms-{recipient.recipient_id}",
            timestamp=datetime.now(UTC),
        )

    async def get_capabilities(self, ctx: Any = None) -> ChannelCapabilities:
        """Retorna capacidades do canal."""
        provider = self._get_provider(ctx)
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=False,
            supports_rich_content=False,
            supports_attachments=False,
            supports_interactive=False,
            max_message_length=160,  # SMS padrão
            metadata={
                "format": "plain",
                "provider": provider,
                "implementation": "stub",
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient, ctx: Any = None) -> RecipientValidation:
        """Valida destinatário (stub)."""
        phone = recipient.channels.get("sms")
        
        if not phone:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel_address=phone,
                error_message="Telefone não encontrado no destinatário",
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
