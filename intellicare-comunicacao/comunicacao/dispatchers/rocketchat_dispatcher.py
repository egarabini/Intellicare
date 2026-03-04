"""Dispatcher para Rocket.Chat - stack oficial V5."""

from __future__ import annotations

import logging
from typing import Any
from datetime import UTC, datetime

from comunicacao.dispatchers.base import (
    ChannelCapabilities,
    ChannelHealth,
    ChannelMessage,
    DeliveryStatus,
    DispatchResult,
    RecipientValidation,
    RenderedContent,
    ResolvedRecipient,
)
from comunicacao.rocketchat.client import RocketChatAPIError, RocketChatClient
from comunicacao.rocketchat.config import RocketChatConfig

logger = logging.getLogger(__name__)


class RocketChatDispatcher:
    """Dispatcher para Rocket.Chat com envio real via API REST."""

    channel = "rocketchat"

    def __init__(
        self,
        config: RocketChatConfig | None = None,
        client: RocketChatClient | None = None,
    ) -> None:
        self._config = config or RocketChatConfig.from_env()
        self._client = client or RocketChatClient(self._config)
        self._message_room_map: dict[str, str] = {}
        self._status_map: dict[str, DeliveryStatus] = {}
        logger.info("RocketChatDispatcher inicializado - server=%s", self._config.url)

    async def send(self, message: ChannelMessage, ctx: Any = None) -> DispatchResult:
        room_id = message.recipient.channels.get("rocketchat")
        if not room_id:
            room_id = message.metadata.get("room_id") if isinstance(message.metadata, dict) else None
        if not room_id:
            return DispatchResult(
                success=False,
                error_code="no_room_id",
                error_message=f"Room ID nao encontrado para {message.recipient.recipient_id}",
                timestamp=datetime.now(UTC),
            )
        try:
            response = await self._client.send_message(
                room_id=room_id,
                text=message.content.body,
                alias="IntelliCare",
                emoji=":robot:",
            )
            self._message_room_map[response.message_id] = response.channel_id or room_id
            self._status_map[response.message_id] = DeliveryStatus.SENT
            return DispatchResult(
                success=True,
                channel_message_id=response.message_id,
                channel_room_id=response.channel_id or room_id,
                timestamp=datetime.now(UTC),
                metadata={"server": self._config.url, "room_id": room_id},
            )
        except RocketChatAPIError as exc:
            return DispatchResult(
                success=False,
                error_code="rocketchat_api_error",
                error_message=str(exc),
                channel_room_id=room_id,
                timestamp=datetime.now(UTC),
            )
        except Exception as exc:
            logger.exception("Falha inesperada no envio Rocket.Chat")
            return DispatchResult(
                success=False,
                error_code="rocketchat_unexpected_error",
                error_message=str(exc),
                channel_room_id=room_id,
                timestamp=datetime.now(UTC),
            )

    async def get_status(self, channel_message_id: str, ctx: Any = None) -> DeliveryStatus:
        return self._status_map.get(channel_message_id, DeliveryStatus.UNKNOWN)

    async def cancel(self, channel_message_id: str, ctx: Any = None) -> bool:
        room_id = self._message_room_map.get(channel_message_id)
        if not room_id:
            return False
        deleted = await self._client.delete_message(channel_message_id, room_id)
        if deleted:
            self._status_map[channel_message_id] = DeliveryStatus.SKIPPED
        return deleted

    async def health_check(self, ctx: Any = None) -> ChannelHealth:
        try:
            health = await self._client.health_check_details()
            available = bool(health.get("healthy"))
            status = "up" if available else "down"
            return ChannelHealth(
                channel=self.channel,
                available=available,
                status=status,
                details={
                    "server": self._config.url,
                    "version": health.get("version", "unknown"),
                    "latency_ms": health.get("latency_ms", -1),
                },
            )
        except Exception as exc:
            return ChannelHealth(
                channel=self.channel,
                available=False,
                status="down",
                details={"server": self._config.url, "error": str(exc)},
            )

    async def test_send(self, recipient: ResolvedRecipient, ctx: Any = None) -> DispatchResult:
        message = ChannelMessage(
            intent_id="test-intent",
            correlation_id="test-correlation",
            channel=self.channel,
            recipient=recipient,
            content=RenderedContent(
                format="markdown",
                body="Teste de conexao IntelliCare no Rocket.Chat",
            ),
        )
        return await self.send(message)

    async def get_capabilities(self, ctx: Any = None) -> ChannelCapabilities:
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=True,
            supports_rich_content=True,
            supports_attachments=True,
            supports_interactive=True,
            max_message_length=5000,
            metadata={
                "format": "markdown",
                "server": self._config.url,
                "version": "7.13.2",
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient, ctx: Any = None) -> RecipientValidation:
        room_id = recipient.channels.get("rocketchat")
        if not room_id:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                error_message="Room ID nao encontrado no destinatario",
            )
        if not (room_id.startswith("@") or room_id.startswith("#") or len(room_id) > 8):
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                channel_address=room_id,
                error_message=f"Room ID invalido: {room_id}",
            )
        return RecipientValidation(
            valid=True,
            recipient_id=recipient.recipient_id,
            channel_address=room_id,
        )
