"""
SMS Dispatcher (D4).

Implementa ChannelDispatcher para SMS com múltiplos providers.
"""

import logging
from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.models import ExternalMessageLog, ExternalMessageStatus
from comunicacao.channels.sms.config import SMSConfig
from comunicacao.channels.sms.providers import (
    BaseSMSProvider,
    TwilioSMSProvider,
    ZenviaSMSProvider,
    SNSSMSProvider,
)
from comunicacao.dispatchers.base import (
    ChannelMessage,
    DispatchResult,
    DeliveryStatus,
    ChannelHealth,
    ChannelCapabilities,
    ResolvedRecipient,
    RecipientValidation,
    RenderedContent,
    ChannelDispatcher,
)

logger = logging.getLogger(__name__)


class SMSDispatcher(ChannelDispatcher):
    """Dispatcher para SMS com múltiplos providers."""

    channel = "sms"

    def __init__(self, db: AsyncSession, config: SMSConfig):
        """
        Inicializa dispatcher.

        Args:
            db: Sessão do banco.
            config: Configuração SMS.
        """
        self._db = db
        self._config = config
        self._providers: dict[str, BaseSMSProvider] = {}

        # Inicializar providers disponíveis
        if config.twilio and config.twilio.enabled:
            self._providers["twilio"] = TwilioSMSProvider(config.twilio)

        if config.zenvia and config.zenvia.enabled:
            self._providers["zenvia"] = ZenviaSMSProvider(config.zenvia)

        if config.sns and config.sns.enabled:
            self._providers["sns"] = SNSSMSProvider(config.sns)

        if not self._providers:
            logger.warning("Nenhum provider SMS configurado!")

    async def send(self, message: ChannelMessage) -> DispatchResult:
        """
        Envia SMS usando provider configurado.

        Args:
            message: Mensagem a enviar.

        Returns:
            DispatchResult: Resultado do envio.
        """
        try:
            # Extrair dados
            phone_number = message.recipient.recipient_id
            text = message.content.body

            # Truncar se necessário
            if len(text) > self._config.max_message_length:
                text = text[: self._config.max_message_length - 3] + "..."

            # Selecionar provider
            provider_name = message.metadata.get("provider", self._config.default_provider)
            provider = self._providers.get(provider_name)

            if not provider:
                # Tentar fallback
                for fallback_name in self._config.fallback_providers:
                    provider = self._providers.get(fallback_name)
                    if provider:
                        provider_name = fallback_name
                        logger.info("Usando fallback provider: %s", provider_name)
                        break

            if not provider:
                return DispatchResult(
                    success=False,
                    error_code="no_provider",
                    error_message="Nenhum provider SMS disponível",
                )

            # Enviar via provider
            logger.info("Enviando SMS: to=%s, provider=%s", phone_number, provider_name)
            result = await provider.send(to=phone_number, text=text)

            # Criar log
            log = ExternalMessageLog(
                channel=self.channel,
                direction="outbound",
                intent_id=message.intent_id,
                correlation_id=message.correlation_id,
                recipient_id=phone_number,
                provider_message_id=result["message_id"],
                status=ExternalMessageStatus.SENT,
                message_content={"text": text, "provider": provider_name},
                sent_at=datetime.now(UTC),
            )

            self._db.add(log)
            await self._db.commit()

            logger.info("SMS enviado: message_id=%s, provider=%s", result["message_id"], provider_name)

            return DispatchResult(
                success=True,
                channel_message_id=result["message_id"],
                metadata={
                    "provider": provider_name,
                    "text_length": len(text),
                },
            )

        except Exception as exc:
            logger.error("Erro ao enviar SMS: %s", exc, exc_info=True)
            return DispatchResult(
                success=False,
                error_code="send_failed",
                error_message=str(exc),
            )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        """
        Consulta status de mensagem.

        Args:
            channel_message_id: ID da mensagem.

        Returns:
            DeliveryStatus: Status da mensagem.
        """
        # Consultar no banco
        stmt = select(ExternalMessageLog).where(
            ExternalMessageLog.provider_message_id == channel_message_id
        )
        result = await self._db.execute(stmt)
        log = result.scalar_one_or_none()

        if not log:
            return DeliveryStatus.UNKNOWN

        # Mapear status
        status_map = {
            ExternalMessageStatus.PENDING: DeliveryStatus.PENDING,
            ExternalMessageStatus.SENT: DeliveryStatus.SENT,
            ExternalMessageStatus.DELIVERED: DeliveryStatus.DELIVERED,
            ExternalMessageStatus.FAILED: DeliveryStatus.FAILED,
        }

        return status_map.get(log.status, DeliveryStatus.UNKNOWN)

    async def cancel(self, channel_message_id: str) -> bool:
        """
        SMS não suporta cancelamento após envio.

        Args:
            channel_message_id: ID da mensagem.

        Returns:
            bool: Sempre False.
        """
        logger.warning("SMS não suporta cancelamento: %s", channel_message_id)
        return False

    async def health_check(self) -> ChannelHealth:
        """
        Verifica saúde do canal SMS.

        Returns:
            ChannelHealth: Status de saúde.
        """
        # Verificar cada provider
        provider_status = {}
        any_available = False

        for name, provider in self._providers.items():
            is_healthy = await provider.health_check()
            provider_status[name] = "ok" if is_healthy else "error"
            if is_healthy:
                any_available = True

        return ChannelHealth(
            channel=self.channel,
            available=any_available,
            status="healthy" if any_available else "unavailable",
            details={
                "providers": provider_status,
                "default_provider": self._config.default_provider,
            },
        )

    async def test_send(self, recipient: ResolvedRecipient) -> DispatchResult:
        """
        Envia mensagem de teste.

        Args:
            recipient: Destinatário.

        Returns:
            DispatchResult: Resultado do envio.
        """
        message = ChannelMessage(
            intent_id="test-intent",
            correlation_id=f"test-{uuid4()}",
            channel=self.channel,
            recipient=recipient,
            content=RenderedContent(
                format="text",
                body="Esta é uma mensagem de teste do IntelliCare.",
                subject="Teste IntelliCare",
            ),
            metadata={"test": True},
        )

        return await self.send(message)

    async def get_capabilities(self) -> ChannelCapabilities:
        """
        Retorna capacidades do canal.

        Returns:
            ChannelCapabilities: Capacidades.
        """
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=False,  # Depende do provider
            supports_rich_content=False,  # Apenas texto
            supports_attachments=False,
            supports_interactive=False,
            max_message_length=self._config.max_message_length,
            metadata={
                "providers": list(self._providers.keys()),
                "default_provider": self._config.default_provider,
                "fallback_providers": self._config.fallback_providers,
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation:
        """
        Valida se destinatário é válido para SMS.

        Args:
            recipient: Destinatário a validar.

        Returns:
            RecipientValidation: Resultado da validação.
        """
        phone_number = recipient.recipient_id

        # Validar formato (+55...)
        if not phone_number.startswith("+"):
            return RecipientValidation(
                valid=False,
                recipient_id=phone_number,
                error_code="invalid_format",
                error_message="Número deve começar com + (formato internacional)",
            )

        # Remover + e verificar dígitos
        digits = phone_number[1:]
        if not digits.isdigit():
            return RecipientValidation(
                valid=False,
                recipient_id=phone_number,
                error_code="invalid_chars",
                error_message="Número deve conter apenas dígitos após +",
            )

        if len(digits) < 10:
            return RecipientValidation(
                valid=False,
                recipient_id=phone_number,
                error_code="too_short",
                error_message="Número muito curto (mínimo 10 dígitos)",
            )

        return RecipientValidation(valid=True, recipient_id=phone_number)

