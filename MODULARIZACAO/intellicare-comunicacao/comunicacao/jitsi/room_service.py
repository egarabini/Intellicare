"""Serviço de gerenciamento de salas Jitsi."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from comunicacao.jitsi.client import JitsiClient
from comunicacao.jitsi.config import JitsiConfig
from comunicacao.jitsi.models import (
    JitsiParticipant,
    JitsiParticipantCreate,
    JitsiRoom,
    JitsiRoomCreate,
    JitsiRoomResponse,
    ParticipantRole,
    RoomStatus,
)


class RoomService:
    """
    Serviço de gerenciamento de salas Jitsi.
    
    Responsabilidades:
    - CRUD de salas
    - Gerenciamento de participantes
    - Agendamento e validação
    - Transições de status
    """
    
    def __init__(self, db: AsyncSession, config: JitsiConfig):
        """
        Inicializa serviço.
        
        Args:
            db: Sessão do banco de dados
            config: Configuração do Jitsi
        """
        self._db = db
        self._config = config
        self._client = JitsiClient(config)
    
    async def create_room(
        self,
        room_data: JitsiRoomCreate,
        intent_id: str | None = None,
    ) -> JitsiRoom:
        """
        Cria nova sala Jitsi.
        
        Args:
            room_data: Dados da sala
            intent_id: ID da intent de comunicação (opcional)
        
        Returns:
            Sala criada
        
        Raises:
            ValueError: Se configuração inválida
        """
        # Validar configuração
        errors = self._client.validate_room_config(
            room_data.scheduled_start,
            room_data.scheduled_end,
            room_data.max_participants,
        )
        
        if errors:
            raise ValueError(f"Configuração inválida: {', '.join(errors)}")
        
        # Gerar nome único
        room_name = self._client.generate_room_name(room_data.room_type)
        
        # Criar sala
        room = JitsiRoom(
            room_name=room_name,
            room_type=room_data.room_type,
            status=RoomStatus.SCHEDULED,
            scheduled_start=room_data.scheduled_start,
            scheduled_end=room_data.scheduled_end,
            title=room_data.title,
            description=room_data.description,
            patient_id=room_data.patient_id,
            intent_id=intent_id,
            max_participants=room_data.max_participants,
            enable_recording=room_data.enable_recording,
            enable_lobby=room_data.enable_lobby,
            enable_chat=room_data.enable_chat,
            enable_screen_sharing=room_data.enable_screen_sharing,
            moderator_password=room_data.moderator_password,
            metadata=room_data.metadata,
        )
        
        self._db.add(room)
        await self._db.commit()
        await self._db.refresh(room)
        
        return room
    
    async def get_room(self, room_id: UUID) -> JitsiRoom | None:
        """
        Busca sala por ID.
        
        Args:
            room_id: ID da sala
        
        Returns:
            Sala encontrada ou None
        """
        stmt = (
            select(JitsiRoom)
            .where(JitsiRoom.id == room_id)
            .options(selectinload(JitsiRoom.participants))
        )
        
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_room_by_name(self, room_name: str) -> JitsiRoom | None:
        """
        Busca sala por nome.
        
        Args:
            room_name: Nome da sala
        
        Returns:
            Sala encontrada ou None
        """
        stmt = (
            select(JitsiRoom)
            .where(JitsiRoom.room_name == room_name)
            .options(selectinload(JitsiRoom.participants))
        )
        
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_rooms(
        self,
        status: RoomStatus | None = None,
        patient_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JitsiRoom]:
        """
        Lista salas com filtros.
        
        Args:
            status: Filtrar por status (opcional)
            patient_id: Filtrar por paciente (opcional)
            limit: Limite de resultados
            offset: Offset para paginação
        
        Returns:
            Lista de salas
        """
        stmt = select(JitsiRoom).options(selectinload(JitsiRoom.participants))
        
        # Aplicar filtros
        filters = []
        if status:
            filters.append(JitsiRoom.status == status)
        if patient_id:
            filters.append(JitsiRoom.patient_id == patient_id)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        # Ordenar por data de início
        stmt = stmt.order_by(JitsiRoom.scheduled_start.desc())
        
        # Paginação
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def add_participant(
        self,
        room_id: UUID,
        participant_data: JitsiParticipantCreate,
        expires_in_minutes: int = 60,
    ) -> JitsiParticipant:
        """
        Adiciona participante à sala.

        Args:
            room_id: ID da sala
            participant_data: Dados do participante
            expires_in_minutes: Tempo de expiração do token JWT

        Returns:
            Participante criado

        Raises:
            ValueError: Se sala não encontrada ou lotada
        """
        # Buscar sala
        room = await self.get_room(room_id)
        if not room:
            raise ValueError(f"Sala {room_id} não encontrada")

        # Verificar limite de participantes
        if len(room.participants) >= room.max_participants:
            raise ValueError(f"Sala lotada (máximo: {room.max_participants})")

        # Gerar token JWT
        jwt_token = self._client.generate_jwt_token(
            room_name=room.room_name,
            user_id=participant_data.user_id,
            user_name=participant_data.user_name,
            role=participant_data.role,
            expires_in_minutes=expires_in_minutes,
            user_email=participant_data.user_email,
        )

        # Calcular expiração
        from datetime import timedelta
        token_expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)

        # Criar participante
        participant = JitsiParticipant(
            room_id=room_id,
            user_id=participant_data.user_id,
            user_name=participant_data.user_name,
            user_email=participant_data.user_email,
            role=participant_data.role,
            jwt_token=jwt_token,
            token_expires_at=token_expires_at,
        )

        self._db.add(participant)
        await self._db.commit()
        await self._db.refresh(participant)

        return participant

    async def remove_participant(self, participant_id: UUID) -> bool:
        """
        Remove participante da sala.

        Args:
            participant_id: ID do participante

        Returns:
            True se removido, False se não encontrado
        """
        stmt = select(JitsiParticipant).where(JitsiParticipant.id == participant_id)
        result = await self._db.execute(stmt)
        participant = result.scalar_one_or_none()

        if not participant:
            return False

        await self._db.delete(participant)
        await self._db.commit()

        return True

    async def mark_participant_joined(self, room_id: UUID, user_id: str) -> bool:
        """
        Marca participante como conectado.

        Args:
            room_id: ID da sala
            user_id: ID do usuário participante

        Returns:
            True se participante encontrado e atualizado
        """
        stmt = select(JitsiParticipant).where(
            and_(
                JitsiParticipant.room_id == room_id,
                JitsiParticipant.user_id == user_id,
            )
        )
        result = await self._db.execute(stmt)
        participant = result.scalar_one_or_none()
        if participant is None:
            return False
        if participant.joined_at is None:
            participant.joined_at = datetime.utcnow()
        participant.left_at = None
        await self._db.commit()
        return True

    async def mark_participant_left(self, room_id: UUID, user_id: str) -> bool:
        """
        Marca participante como desconectado.

        Args:
            room_id: ID da sala
            user_id: ID do usuário participante

        Returns:
            True se participante encontrado e atualizado
        """
        stmt = select(JitsiParticipant).where(
            and_(
                JitsiParticipant.room_id == room_id,
                JitsiParticipant.user_id == user_id,
            )
        )
        result = await self._db.execute(stmt)
        participant = result.scalar_one_or_none()
        if participant is None:
            return False
        participant.left_at = datetime.utcnow()
        await self._db.commit()
        return True

    async def start_room(self, room_id: UUID) -> JitsiRoom:
        """
        Inicia sala (marca como ACTIVE).

        Args:
            room_id: ID da sala

        Returns:
            Sala atualizada

        Raises:
            ValueError: Se sala não encontrada ou já iniciada
        """
        room = await self.get_room(room_id)
        if not room:
            raise ValueError(f"Sala {room_id} não encontrada")

        if room.status != RoomStatus.SCHEDULED:
            raise ValueError(f"Sala já está {room.status.value}")

        room.status = RoomStatus.ACTIVE
        room.actual_start = datetime.utcnow()

        await self._db.commit()
        await self._db.refresh(room)

        return room

    async def end_room(self, room_id: UUID) -> JitsiRoom:
        """
        Finaliza sala (marca como COMPLETED).

        Args:
            room_id: ID da sala

        Returns:
            Sala atualizada

        Raises:
            ValueError: Se sala não encontrada ou não ativa
        """
        room = await self.get_room(room_id)
        if not room:
            raise ValueError(f"Sala {room_id} não encontrada")

        if room.status != RoomStatus.ACTIVE:
            raise ValueError(f"Sala não está ativa (status: {room.status.value})")

        room.status = RoomStatus.COMPLETED
        room.actual_end = datetime.utcnow()

        await self._db.commit()
        await self._db.refresh(room)

        return room

    async def cancel_room(self, room_id: UUID) -> JitsiRoom:
        """
        Cancela sala (marca como CANCELLED).

        Args:
            room_id: ID da sala

        Returns:
            Sala atualizada

        Raises:
            ValueError: Se sala não encontrada ou já finalizada
        """
        room = await self.get_room(room_id)
        if not room:
            raise ValueError(f"Sala {room_id} não encontrada")

        if room.status in (RoomStatus.COMPLETED, RoomStatus.CANCELLED):
            raise ValueError(f"Sala já está {room.status.value}")

        room.status = RoomStatus.CANCELLED

        await self._db.commit()
        await self._db.refresh(room)

        return room

    def build_room_response(self, room: JitsiRoom) -> JitsiRoomResponse:
        """
        Constrói response de sala.

        Args:
            room: Sala

        Returns:
            Response formatado
        """
        return JitsiRoomResponse(
            id=room.id,
            room_name=room.room_name,
            room_type=room.room_type,
            status=room.status,
            scheduled_start=room.scheduled_start,
            scheduled_end=room.scheduled_end,
            actual_start=room.actual_start,
            actual_end=room.actual_end,
            title=room.title,
            description=room.description,
            patient_id=room.patient_id,
            intent_id=room.intent_id,
            room_url=self._client.get_room_url(room.room_name),
            participant_count=len(room.participants) if room.participants else 0,
        )
