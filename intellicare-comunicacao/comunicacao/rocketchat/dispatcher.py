"""Dispatcher completo para Rocket.Chat v7.13.2."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from comunicacao.dispatchers.base import (
    ChannelCapabilities,
    ChannelHealth,
    ChannelMessage,
    DeliveryStatus,
    DispatchResult,
    RecipientValidation,
    ResolvedRecipient,
)
from comunicacao.rocketchat.client import RocketChatAPIError, RocketChatClient
from comunicacao.rocketchat.config import RocketChatConfig
from comunicacao.rocketchat.models import RCAttachment

logger = logging.getLogger(__name__)


class RocketChatDispatcher:
    """
    Dispatcher para Rocket.Chat v7.13.2.
    
    Stack oficial V5 - rocket.gsi.srv.br
    Implementação completa com RocketChatClient.
    """

    channel = "rocketchat"

    def __init__(
        self,
        config: RocketChatConfig | None = None,
        client: RocketChatClient | None = None,
    ) -> None:
        """
        Inicializa dispatcher.
        
        Args:
            config: Configuração do RC (se None, usa from_env())
            client: Cliente RC (se None, cria novo)
        """
        if config is None:
            config = RocketChatConfig.from_env()
        
        self.config = config
        self.client = client or RocketChatClient(config)
        
        logger.info(
            "RocketChatDispatcher inicializado - server=%s",
            config.url,
        )

    async def send(self, message: ChannelMessage) -> DispatchResult:
        """
        Envia mensagem via Rocket.Chat.
        
        Args:
            message: ChannelMessage com recipient, content, metadata
        
        Returns:
            DispatchResult com sucesso/erro
        """
        logger.info(
            "RocketChatDispatcher.send: intent=%s, recipient=%s",
            message.intent_id,
            message.recipient.recipient_id,
        )

        # Extrai room_id do destinatário
        room_id = message.recipient.channels.get("rocketchat")
        
        if not room_id:
            logger.error("RocketChatDispatcher: room_id não encontrado para %s", message.recipient.recipient_id)
            return DispatchResult(
                success=False,
                channel=self.channel,
                error_code="no_room_id",
                error_message=f"Room ID não encontrado para {message.recipient.recipient_id}",
                timestamp=datetime.now(UTC),
            )

        try:
            # Prepara attachments se houver
            attachments = []
            if message.content.attachments:
                for att in message.content.attachments:
                    attachments.append(
                        RCAttachment(
                            title=att.get("title"),
                            text=att.get("text"),
                            color=att.get("color"),
                            fields=att.get("fields", []),
                        )
                    )
            
            # Envia mensagem via client
            response = await self.client.send_message(
                room_id=room_id,
                text=message.content.text,
                alias="IntelliCare",
                emoji=":robot:",
                attachments=attachments if attachments else None,
            )
            
            logger.info("Mensagem enviada com sucesso: message_id=%s", response.message_id)
            
            return DispatchResult(
                success=True,
                channel=self.channel,
                channel_message_id=response.message_id,
                channel_room_id=response.channel_id,
                timestamp=datetime.now(UTC),
                metadata={
                    "server": self.config.url,
                    "room_id": room_id,
                },
            )
            
        except RocketChatAPIError as e:
            logger.error("Erro ao enviar mensagem: %s", str(e))
            return DispatchResult(
                success=False,
                channel=self.channel,
                error_code="api_error",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )
        except Exception as e:
            logger.exception("Erro inesperado ao enviar mensagem")
            return DispatchResult(
                success=False,
                channel=self.channel,
                error_code="unexpected_error",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        """
        Consulta status de entrega.
        
        Args:
            channel_message_id: ID da mensagem no RC
        
        Returns:
            DeliveryStatus (SENT por padrão, RC não tem API de read receipt)
        """
        logger.info("RocketChatDispatcher.get_status: message_id=%s", channel_message_id)

        # Rocket.Chat não tem API pública para verificar read receipts
        # Retornamos SENT como padrão
        return DeliveryStatus.SENT

    async def cancel(self, channel_message_id: str, room_id: str | None = None) -> bool:
        """
        Cancela/deleta mensagem.

        Args:
            channel_message_id: ID da mensagem no RC
            room_id: ID do canal (necessário para deletar)

        Returns:
            True se sucesso
        """
        logger.info("RocketChatDispatcher.cancel: message_id=%s", channel_message_id)

        if not room_id:
            logger.error("room_id é necessário para deletar mensagem")
            return False

        try:
            return await self.client.delete_message(channel_message_id, room_id)
        except Exception as e:
            logger.error("Erro ao deletar mensagem: %s", str(e))
            return False

    async def health_check(self) -> ChannelHealth:
        """
        Verifica saúde do servidor Rocket.Chat.

        Returns:
            ChannelHealth com status, latência e versão
        """
        logger.info("RocketChatDispatcher.health_check: server=%s", self.config.url)

        try:
            health = await self.client.health_check()

            return ChannelHealth(
                channel=self.channel,
                healthy=health["healthy"],
                latency_ms=health["latency_ms"],
                details={
                    "server": self.config.url,
                    "version": health.get("version", "unknown"),
                    "authenticated": health.get("details", {}).get("authenticated", False),
                },
            )
        except Exception as e:
            logger.error("Health check falhou: %s", str(e))
            return ChannelHealth(
                channel=self.channel,
                healthy=False,
                latency_ms=-1,
                details={
                    "server": self.config.url,
                    "error": str(e),
                },
            )

    async def test_send(self, recipient: ResolvedRecipient) -> DispatchResult:
        """
        Envia mensagem de teste.

        Args:
            recipient: Destinatário com room_id

        Returns:
            DispatchResult
        """
        logger.info("RocketChatDispatcher.test_send: recipient=%s", recipient.recipient_id)

        room_id = recipient.channels.get("rocketchat")

        if not room_id:
            return DispatchResult(
                success=False,
                channel=self.channel,
                error_code="no_room_id",
                error_message="Room ID não encontrado",
                timestamp=datetime.now(UTC),
            )

        try:
            response = await self.client.send_message(
                room_id=room_id,
                text="🤖 **Teste de Conexão IntelliCare**\n\nSe você está vendo esta mensagem, a integração está funcionando!",
                alias="IntelliCare Bot",
                emoji=":robot:",
            )

            return DispatchResult(
                success=True,
                channel=self.channel,
                channel_message_id=response.message_id,
                channel_room_id=response.channel_id,
                timestamp=datetime.now(UTC),
            )
        except Exception as e:
            logger.error("Erro ao enviar mensagem de teste: %s", str(e))
            return DispatchResult(
                success=False,
                channel=self.channel,
                error_code="test_send_failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

    async def get_capabilities(self) -> ChannelCapabilities:
        """
        Retorna capacidades do Rocket.Chat.

        Returns:
            ChannelCapabilities
        """
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=True,
            supports_rich_content=True,  # Markdown, attachments
            supports_attachments=True,
            supports_interactive=True,  # Botões, ações
            max_message_length=5000,
            metadata={
                "format": "markdown",
                "server": self.config.url,
                "version": "7.13.2",
                "bot_support": True,
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation:
        """
        Valida destinatário.

        Args:
            recipient: Destinatário a validar

        Returns:
            RecipientValidation
        """
        room_id = recipient.channels.get("rocketchat")

        if not room_id:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel=self.channel,
                error_message="Room ID não encontrado no destinatário",
            )

        # Validação básica de formato
        # Room IDs no Rocket.Chat podem ser: @username, #channel, ou ID direto
        if not (room_id.startswith("@") or room_id.startswith("#") or len(room_id) > 10):
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel=self.channel,
                error_message=f"Room ID inválido: {room_id}",
            )

        return RecipientValidation(
            valid=True,
            recipient_id=recipient.recipient_id,
            channel=self.channel,
            normalized_address=room_id,
        )

