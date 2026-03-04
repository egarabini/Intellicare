"""Dispatcher Matrix baseado no MatrixClientService existente."""

from __future__ import annotations

from comunicacao.dispatchers.base import (
    ChannelHealth,
    ChannelMessage,
    DeliveryStatus,
    DispatchResult,
)
from comunicacao.matrix_client import MatrixClientService


class MatrixDispatcher:
    """Implementacao concreta do contrato de canal para Matrix."""

    channel = "matrix"

    def __init__(self, matrix: MatrixClientService) -> None:
        self._matrix = matrix

    async def send(self, message: ChannelMessage, ctx: Any = None) -> DispatchResult:
        room_id = self._resolve_room_id(message=message)
        if not room_id:
            return DispatchResult(
                success=False,
                error_code="missing_room_id",
                error_message="room_id nao encontrado para envio matrix",
            )
        result = await self._matrix.send_text_message(room_id=room_id, message=message.content.body)
        if result.get("ok"):
            return DispatchResult(
                success=True,
                channel_message_id=result.get("event_id"),
                channel_room_id=room_id,
                metadata={"provider_response": result},
            )
        return DispatchResult(
            success=False,
            channel_room_id=room_id,
            error_code="matrix_send_failed",
            error_message=str(result.get("error", "falha no envio matrix")),
            metadata={"provider_response": result},
        )

    async def is_available(self) -> bool:
        ensure_login = getattr(self._matrix, "ensure_login", None)
        if callable(ensure_login):
            return bool(await ensure_login())
        return False

    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        if channel_message_id:
            return DeliveryStatus.SENT
        return DeliveryStatus.UNKNOWN

    async def get_health(self) -> ChannelHealth:
        available = await self.is_available()
        status = "up" if available else "down"
        return ChannelHealth(channel=self.channel, available=available, status=status)

    async def supports_read_receipt(self) -> bool:
        return False

    async def supports_rich_content(self) -> bool:
        return True

    def _resolve_room_id(self, message: ChannelMessage) -> str | None:
        from_recipient = message.recipient.channels.get(self.channel)
        if from_recipient:
            return from_recipient
        metadata = message.metadata
        room_id = metadata.get("room_id") if isinstance(metadata, dict) else None
        if isinstance(room_id, str) and room_id:
            return room_id
        return None
