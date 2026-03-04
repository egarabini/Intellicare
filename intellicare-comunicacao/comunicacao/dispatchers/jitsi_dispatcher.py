"""Dispatcher para criação de salas Jitsi Meet."""

from __future__ import annotations

import logging
from typing import Any
from datetime import UTC, datetime
from uuid import uuid4

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


class JitsiDispatcher:
    """
    Dispatcher para criação de salas Jitsi Meet.
    
    Implementação stub - será completada na Fase 3 (D3 - Teleconsulta/Vídeo).
    """

    channel = "jitsi"

    def __init__(self, jitsi_url: str = "https://meet.gsi.srv.br") -> None:
        self.jitsi_url = jitsi_url
        logger.info("JitsiDispatcher inicializado (stub) - url=%s", jitsi_url)

    async def send(self, message: ChannelMessage, ctx: Any = None) -> DispatchResult:
        """
        Cria sala Jitsi e envia convite (stub).
        
        Na implementação real, criará sala e enviará link via outro canal.
        """
        logger.info(
            "JitsiDispatcher.send (stub): intent=%s, recipient=%s",
            message.intent_id,
            message.recipient.recipient_id,
        )

        # Gera ID único para a sala
        room_id = f"room-{uuid4().hex[:12]}"
        room_url = f"{self.jitsi_url}/{room_id}"

        # Stub - retorna sucesso simulado
        return DispatchResult(
            success=True,
            channel_message_id=f"jitsi-{message.intent_id}",
            channel_room_id=room_id,
            timestamp=datetime.now(UTC),
            metadata={"room_url": room_url},
        )

    async def get_status(self, channel_message_id: str, ctx: Any = None) -> DeliveryStatus:
        """Consulta status da sala (stub)."""
        logger.info("JitsiDispatcher.get_status (stub): message_id=%s", channel_message_id)
        return DeliveryStatus.SENT

    async def cancel(self, channel_message_id: str, ctx: Any = None) -> bool:
        """Cancela/fecha sala (stub)."""
        logger.info("JitsiDispatcher.cancel (stub): message_id=%s", channel_message_id)
        return True  # Salas podem ser fechadas

    async def health_check(self, ctx: Any = None) -> ChannelHealth:
        """Verifica saúde do servidor Jitsi (stub)."""
        return ChannelHealth(
            channel=self.channel,
            available=True,
            status="up",
            details={"jitsi_url": self.jitsi_url, "status": "stub", "latency_ms": 30},
        )

    async def test_send(self, recipient: ResolvedRecipient, ctx: Any = None) -> DispatchResult:
        """Cria sala de teste (stub)."""
        logger.info("JitsiDispatcher.test_send (stub): recipient=%s", recipient.recipient_id)
        
        room_id = f"test-room-{uuid4().hex[:8]}"
        
        return DispatchResult(
            success=True,
            channel_message_id=f"test-jitsi-{recipient.recipient_id}",
            channel_room_id=room_id,
            timestamp=datetime.now(UTC),
            metadata={"room_url": f"{self.jitsi_url}/{room_id}"},
        )

    async def get_capabilities(self, ctx: Any = None) -> ChannelCapabilities:
        """Retorna capacidades do canal."""
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=False,
            supports_rich_content=False,
            supports_attachments=False,
            supports_interactive=True,  # Vídeo/áudio interativo
            max_message_length=None,
            metadata={
                "format": "video_call",
                "jitsi_url": self.jitsi_url,
                "implementation": "stub",
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient, ctx: Any = None) -> RecipientValidation:
        """Valida destinatário (stub)."""
        # Para Jitsi, qualquer destinatário é válido (sala pode ser criada)
        # Na implementação real, verificaria se o destinatário tem acesso
        
        return RecipientValidation(
            valid=True,
            recipient_id=recipient.recipient_id,
            channel_address=recipient.recipient_id,
            metadata={"can_create_room": True},
        )
