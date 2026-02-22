"""
WhatsApp Dispatcher (D4).

Implementa ChannelDispatcher para WhatsApp Business API.
"""

import json
import logging
from datetime import datetime, UTC, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.models import (
    ExternalMessageLog,
    ExternalMessageStatus,
    WhatsAppSession,
)
from comunicacao.channels.whatsapp.client import WhatsAppClient
from comunicacao.channels.whatsapp.config import WhatsAppConfig
from comunicacao.dispatchers.base import (
    ChannelMessage,
    DispatchResult,
    DeliveryStatus,
    ChannelHealth,
    ChannelCapabilities,
    ResolvedRecipient,
    RecipientValidation,
    RenderedContent,
)
from comunicacao.routing.protocols import ChannelDispatcher

logger = logging.getLogger(__name__)


class WhatsAppDispatcher(ChannelDispatcher):
    """Dispatcher para WhatsApp Business API."""

    channel = "whatsapp"

    def __init__(self, db: AsyncSession, config: WhatsAppConfig):
        """
        Inicializa dispatcher.

        Args:
            db: Sessão do banco.
            config: Configuração WhatsApp.
        """
        self._db = db
        self._config = config
        self._client = WhatsAppClient(config)

    async def send(self, message: ChannelMessage) -> DispatchResult:
        """
        Envia mensagem WhatsApp.

        Args:
            message: Mensagem a enviar.

        Returns:
            DispatchResult: Resultado do envio.
        """
        try:
            # Extrair dados
            phone_number = message.recipient.recipient_id
            template_name = message.metadata.get("template_name")
            template_params = message.metadata.get("template_params", [])

            # Validar template
            if not template_name:
                return DispatchResult(
                    success=False,
                    error_code="missing_template",
                    error_message="template_name é obrigatório no metadata",
                )

            # Enviar via client
            logger.info("Enviando WhatsApp: to=%s, template=%s", phone_number, template_name)
            result = await self._client.send_template_message(
                to=phone_number,
                template_name=template_name,
                params=template_params,
            )

            # Extrair message_id
            provider_message_id = result["messages"][0]["id"]

            # Criar log
            log = ExternalMessageLog(
                channel=self.channel,
                direction="outbound",
                intent_id=message.intent_id,
                correlation_id=message.correlation_id,
                recipient_id=phone_number,
                provider_message_id=provider_message_id,
                status=ExternalMessageStatus.SENT,
                message_content={
                    "template_name": template_name,
                    "template_params": template_params,
                },
                sent_at=datetime.now(UTC),
            )

            self._db.add(log)
            await self._db.commit()

            # Criar/atualizar session (janela 24h)
            await self._update_session(phone_number)

            logger.info("WhatsApp enviado: message_id=%s", provider_message_id)

            return DispatchResult(
                success=True,
                channel_message_id=provider_message_id,
                metadata={
                    "template_name": template_name,
                    "provider": "meta",
                },
            )

        except Exception as exc:
            logger.error("Erro ao enviar WhatsApp: %s", exc, exc_info=True)
            return DispatchResult(
                success=False,
                error_code="send_failed",
                error_message=str(exc),
            )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        """
        Consulta status de mensagem.

        WhatsApp não tem endpoint de consulta. Status vem via webhook.

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
            ExternalMessageStatus.READ: DeliveryStatus.READ,
            ExternalMessageStatus.FAILED: DeliveryStatus.FAILED,
        }

        return status_map.get(log.status, DeliveryStatus.UNKNOWN)

    async def cancel(self, channel_message_id: str) -> bool:
        """
        WhatsApp não suporta cancelamento.

        Args:
            channel_message_id: ID da mensagem.

        Returns:
            bool: Sempre False.
        """
        logger.warning("WhatsApp não suporta cancelamento: %s", channel_message_id)
        return False

    async def health_check(self) -> ChannelHealth:
        """
        Verifica saúde do canal WhatsApp.

        Returns:
            ChannelHealth: Status de saúde.
        """
        available = await self._client.health_check()

        return ChannelHealth(
            channel=self.channel,
            available=available,
            status="healthy" if available else "unavailable",
            details={
                "provider": "meta",
                "api_version": self._config.graph_api_version,
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
            metadata={
                "template_name": "resultado_exame",
                "template_params": [recipient.recipient_id],
                "test": True,
            },
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
            supports_read_receipt=True,  # Via webhook
            supports_rich_content=True,  # Templates com botões, imagens
            supports_attachments=True,  # Imagens, PDFs, etc
            supports_interactive=True,  # Botões, quick replies
            max_message_length=4096,  # Limite WhatsApp
            metadata={
                "provider": "meta",
                "api_version": self._config.graph_api_version,
                "templates_count": 5,
                "session_window_hours": 24,
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation:
        """
        Valida se destinatário é válido para WhatsApp.

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
                reason="Número deve começar com + (formato internacional)",
            )

        if len(phone_number) < 10:
            return RecipientValidation(
                valid=False,
                reason="Número muito curto",
            )

        return RecipientValidation(valid=True)

    async def _update_session(self, phone_number: str) -> None:
        """
        Cria ou atualiza session window (24h).

        Args:
            phone_number: Número do telefone.
        """
        # Buscar session existente
        stmt = select(WhatsAppSession).where(
            WhatsAppSession.phone_number == phone_number,
            WhatsAppSession.active == True,  # noqa: E712
        )
        result = await self._db.execute(stmt)
        session = result.scalar_one_or_none()

        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=24)

        if session:
            # Atualizar session existente
            session.last_message_at = now
            session.expires_at = expires_at
        else:
            # Criar nova session
            session = WhatsAppSession(
                phone_number=phone_number,
                started_at=now,
                last_message_at=now,
                expires_at=expires_at,
                active=True,
            )
            self._db.add(session)

        await self._db.commit()
        logger.info("Session atualizada: phone=%s, expires_at=%s", phone_number, expires_at)

