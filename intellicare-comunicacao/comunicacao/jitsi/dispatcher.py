"""Dispatcher Jitsi para integração com D1 Routing Engine."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

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
from comunicacao.jitsi.client import JitsiClient
from comunicacao.jitsi.config import JitsiConfig
from comunicacao.jitsi.models import (
    JitsiParticipantCreate,
    JitsiRoomCreate,
    ParticipantRole,
    RoomStatus,
    RoomType,
)
from comunicacao.jitsi.room_service import RoomService

logger = logging.getLogger(__name__)


class JitsiDispatcher:
    """
    Dispatcher Jitsi para envio de convites de teleconsulta.
    
    Implementa protocolo ChannelDispatcher do D1.
    
    Responsabilidades:
    - Criar salas Jitsi automaticamente
    - Adicionar participantes
    - Gerar tokens JWT
    - Enviar convites com URL + token
    """
    
    channel = "jitsi"
    
    def __init__(self, db: AsyncSession, config: JitsiConfig | None = None):
        """
        Inicializa dispatcher.
        
        Args:
            db: Sessão do banco de dados
            config: Configuração do Jitsi (usa from_env se None)
        """
        self._db = db
        self._config = config or JitsiConfig.from_env()
        self._client = JitsiClient(self._config)
        self._room_service = RoomService(db, self._config)
    
    async def send(self, message: ChannelMessage) -> DispatchResult:
        """
        Envia convite de teleconsulta via Jitsi.
        
        Fluxo:
        1. Extrai metadados da mensagem (room_type, scheduled_start, etc.)
        2. Cria sala Jitsi (ou usa existente se room_id fornecido)
        3. Adiciona participante com token JWT
        4. Retorna URL + token no metadata
        
        Args:
            message: Mensagem a enviar
        
        Returns:
            DispatchResult com URL da sala e token JWT
        """
        try:
            logger.info(
                "JitsiDispatcher.send: intent=%s, recipient=%s",
                message.intent_id,
                message.recipient.recipient_id,
            )
            
            # Extrair metadados
            metadata = message.metadata or {}
            room_id = metadata.get("room_id")
            
            # Se room_id fornecido, buscar sala existente
            if room_id:
                room = await self._room_service.get_room(room_id)
                if not room:
                    return DispatchResult(
                        success=False,
                        error_code="ROOM_NOT_FOUND",
                        error_message=f"Sala {room_id} não encontrada",
                    )
            else:
                # Criar nova sala
                room_type = RoomType(metadata.get("room_type", "teleconsulta"))
                scheduled_start = metadata.get("scheduled_start", datetime.utcnow())
                scheduled_end = metadata.get("scheduled_end", scheduled_start + timedelta(hours=1))
                title = message.content.title or message.content.subject or "Teleconsulta"
                
                room_data = JitsiRoomCreate(
                    room_type=room_type,
                    scheduled_start=scheduled_start,
                    scheduled_end=scheduled_end,
                    title=title,
                    description=message.content.body[:500] if message.content.body else None,
                    patient_id=metadata.get("patient_id"),
                )
                
                room = await self._room_service.create_room(
                    room_data=room_data,
                    intent_id=message.intent_id,
                )
            
            # Adicionar participante
            user_id = message.recipient.recipient_id
            user_name = message.recipient.metadata.get("name", user_id)
            user_email = message.recipient.channels.get("email")
            role = ParticipantRole(metadata.get("role", "participant"))
            
            participant_data = JitsiParticipantCreate(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                role=role,
            )
            
            participant = await self._room_service.add_participant(
                room_id=room.id,
                participant_data=participant_data,
                expires_in_minutes=metadata.get("token_expires_minutes", 60),
            )
            
            # Gerar URL com token
            room_url = self._client.get_room_url(room.room_name, participant.jwt_token)
            
            logger.info(
                "JitsiDispatcher.send: sala criada room_id=%s, room_name=%s, participant=%s",
                room.id,
                room.room_name,
                participant.id,
            )
            
            return DispatchResult(
                success=True,
                channel_message_id=str(participant.id),
                channel_room_id=str(room.id),
                metadata={
                    "room_id": str(room.id),
                    "room_name": room.room_name,
                    "room_url": room_url,
                    "jwt_token": participant.jwt_token,
                    "token_expires_at": participant.token_expires_at.isoformat() if participant.token_expires_at else None,
                    "participant_id": str(participant.id),
                },
            )
        
        except Exception as e:
            logger.exception("JitsiDispatcher.send: erro ao enviar convite")
            return DispatchResult(
                success=False,
                error_code="JITSI_SEND_ERROR",
                error_message=str(e),
            )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        """
        Consulta status de entrega (participante).

        Args:
            channel_message_id: ID do participante

        Returns:
            Status de entrega
        """
        try:
            from uuid import UUID
            from sqlalchemy import select
            from comunicacao.jitsi.models import JitsiParticipant

            participant_id = UUID(channel_message_id)

            stmt = select(JitsiParticipant).where(JitsiParticipant.id == participant_id)
            result = await self._db.execute(stmt)
            participant = result.scalar_one_or_none()

            if not participant:
                return DeliveryStatus.UNKNOWN

            # Se participante entrou na sala
            if participant.joined_at:
                # Se já saiu
                if participant.left_at:
                    return DeliveryStatus.DELIVERED
                # Ainda na sala
                return DeliveryStatus.READ

            # Convite enviado mas não entrou ainda
            return DeliveryStatus.SENT

        except Exception as e:
            logger.exception("JitsiDispatcher.get_status: erro ao consultar status")
            return DeliveryStatus.UNKNOWN

    async def cancel(self, channel_message_id: str) -> bool:
        """
        Cancela convite (remove participante).

        Args:
            channel_message_id: ID do participante

        Returns:
            True se cancelado
        """
        try:
            from uuid import UUID

            participant_id = UUID(channel_message_id)
            return await self._room_service.remove_participant(participant_id)

        except Exception as e:
            logger.exception("JitsiDispatcher.cancel: erro ao cancelar convite")
            return False

    async def health_check(self) -> ChannelHealth:
        """
        Verifica saúde do canal Jitsi.

        Returns:
            ChannelHealth
        """
        try:
            # Validar configuração
            errors = self._config.validate()

            if errors:
                return ChannelHealth(
                    channel=self.channel,
                    available=False,
                    status="unhealthy",
                    details={"errors": errors},
                )

            # TODO: Fazer ping no servidor Jitsi (opcional)
            # Por enquanto, apenas validar config

            return ChannelHealth(
                channel=self.channel,
                available=True,
                status="healthy",
                details={
                    "base_url": self._config.base_url,
                    "app_id": self._config.app_id,
                },
            )

        except Exception as e:
            logger.exception("JitsiDispatcher.health_check: erro")
            return ChannelHealth(
                channel=self.channel,
                available=False,
                status="unhealthy",
                details={"error": str(e)},
            )

    async def test_send(self, recipient: ResolvedRecipient) -> DispatchResult:
        """
        Envia mensagem de teste.

        Args:
            recipient: Destinatário

        Returns:
            DispatchResult
        """
        # Criar mensagem de teste
        from comunicacao.dispatchers.base import ChannelMessage, RenderedContent

        test_message = ChannelMessage(
            intent_id="test-intent",
            correlation_id="test-correlation",
            channel=self.channel,
            recipient=recipient,
            content=RenderedContent(
                format="markdown",
                body="Mensagem de teste Jitsi",
                title="Teste de Teleconsulta",
            ),
            metadata={
                "room_type": "teleconsulta",
                "scheduled_start": datetime.utcnow(),
                "scheduled_end": datetime.utcnow() + timedelta(minutes=30),
            },
        )

        return await self.send(test_message)

    async def get_capabilities(self) -> ChannelCapabilities:
        """
        Retorna capacidades do canal Jitsi.

        Returns:
            ChannelCapabilities
        """
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=True,  # Podemos saber se participante entrou
            supports_rich_content=True,  # Jitsi suporta vídeo, áudio, chat, screen sharing
            supports_attachments=False,  # Não enviamos anexos no convite
            supports_interactive=True,  # Jitsi é altamente interativo
            max_message_length=None,  # Não há limite para convite
            metadata={
                "supports_video": True,
                "supports_audio": True,
                "supports_chat": self._config.enable_chat,
                "supports_screen_sharing": self._config.enable_screen_sharing,
                "supports_recording": self._config.enable_recording,
                "max_participants": self._config.max_participants,
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation:
        """
        Valida destinatário para Jitsi.

        Args:
            recipient: Destinatário

        Returns:
            RecipientValidation
        """
        # Para Jitsi, qualquer recipient_id é válido
        # Não precisamos de endereço específico (email, telefone, etc.)

        return RecipientValidation(
            valid=True,
            recipient_id=recipient.recipient_id,
            channel_address=recipient.recipient_id,  # Usamos o próprio ID
        )

