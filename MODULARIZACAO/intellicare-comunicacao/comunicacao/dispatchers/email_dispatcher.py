"""Dispatcher para envio de emails."""

from __future__ import annotations

import logging
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


class EmailDispatcher:
    """
    Dispatcher para envio de emails.
    
    Implementação stub - será completada na Fase 4 (D4 - Notificações Externas).
    """

    channel = "email"

    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 587) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        logger.info("EmailDispatcher inicializado (stub) - host=%s, port=%d", smtp_host, smtp_port)

    async def send(self, message: ChannelMessage) -> DispatchResult:
        """Envia email (stub)."""
        logger.info(
            "EmailDispatcher.send (stub): intent=%s, recipient=%s",
            message.intent_id,
            message.recipient.recipient_id,
        )

        # Stub - retorna sucesso simulado
        return DispatchResult(
            success=True,
            channel_message_id=f"email-{message.intent_id}",
            timestamp=datetime.now(UTC),
        )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        """Consulta status de entrega (stub)."""
        logger.info("EmailDispatcher.get_status (stub): message_id=%s", channel_message_id)
        return DeliveryStatus.SENT

    async def cancel(self, channel_message_id: str) -> bool:
        """Cancela envio pendente (stub)."""
        logger.info("EmailDispatcher.cancel (stub): message_id=%s", channel_message_id)
        return False  # Emails não podem ser cancelados após envio

    async def health_check(self) -> ChannelHealth:
        """Verifica saúde do canal (stub)."""
        return ChannelHealth(
            channel=self.channel,
            available=True,
            status="up",
            details={"smtp_host": self.smtp_host, "status": "stub", "latency_ms": 50},
        )

    async def test_send(self, recipient: ResolvedRecipient) -> DispatchResult:
        """Envia mensagem de teste (stub)."""
        logger.info("EmailDispatcher.test_send (stub): recipient=%s", recipient.recipient_id)
        
        return DispatchResult(
            success=True,
            channel_message_id=f"test-email-{recipient.recipient_id}",
            timestamp=datetime.now(UTC),
        )

    async def get_capabilities(self) -> ChannelCapabilities:
        """Retorna capacidades do canal."""
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=True,
            supports_rich_content=True,
            supports_attachments=True,
            supports_interactive=False,
            max_message_length=None,  # Sem limite prático
            metadata={
                "format": "html",
                "smtp_host": self.smtp_host,
                "implementation": "stub",
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation:
        """Valida destinatário (stub)."""
        email = recipient.channels.get("email")
        
        if not email:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel_address=email,
                error_message="Email não encontrado no destinatário",
            )

        # Validação básica de formato
        if "@" not in email:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel_address=email,
                error_message=f"Email inválido: {email}",
            )

        return RecipientValidation(
            valid=True,
            recipient_id=recipient.recipient_id,
            channel_address=email.lower(),
        )
