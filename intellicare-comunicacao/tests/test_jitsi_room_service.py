"""Testes para RoomService."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from comunicacao.jitsi.room_service import RoomService
from comunicacao.jitsi.client import JitsiClient
from comunicacao.jitsi.config import JitsiConfig
from comunicacao.jitsi.models import (
    JitsiRoomCreate,
    JitsiParticipantCreate,
    RoomType,
    RoomStatus,
    ParticipantRole,
)


@pytest.fixture
def jitsi_config():
    """Fixture de configuração Jitsi."""
    return JitsiConfig(
        base_url="https://meet.test.com",
        app_id="test-app",
        app_secret="test-secret",
        default_room_duration_minutes=60,
        max_participants=10,
    )


@pytest.fixture
def jitsi_client(jitsi_config):
    """Fixture de JitsiClient."""
    return JitsiClient(jitsi_config)


@pytest.fixture
async def room_service(async_db_session, jitsi_client):
    """Fixture de RoomService."""
    return RoomService(db=async_db_session, client=jitsi_client)


@pytest.fixture
def room_create_data():
    """Fixture de dados para criar sala."""
    scheduled_start = datetime.utcnow() + timedelta(hours=1)
    scheduled_end = scheduled_start + timedelta(hours=1)
    
    return JitsiRoomCreate(
        room_type=RoomType.TELECONSULTA,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        title="Teleconsulta - Dr. Maria",
        description="Consulta de cardiologia",
        patient_id="patient-123",
        max_participants=5,
    )


class TestRoomService:
    """Testes para RoomService."""
    
    @pytest.mark.asyncio
    async def test_create_room(self, room_service, room_create_data):
        """Testa criação de sala."""
        room = await room_service.create_room(room_create_data)
        
        assert room.id is not None
        assert room.room_name.startswith("intellicare-teleconsulta-")
        assert room.room_type == RoomType.TELECONSULTA
        assert room.status == RoomStatus.SCHEDULED
        assert room.title == "Teleconsulta - Dr. Maria"
        assert room.patient_id == "patient-123"
    
    @pytest.mark.asyncio
    async def test_create_room_with_intent(self, room_service, room_create_data):
        """Testa criação de sala com intent_id."""
        room = await room_service.create_room(
            room_create_data,
            intent_id="intent-456",
        )
        
        assert room.intent_id == "intent-456"
    
    @pytest.mark.asyncio
    async def test_create_room_invalid_dates(self, room_service):
        """Testa criação de sala com datas inválidas."""
        scheduled_start = datetime.utcnow() + timedelta(hours=2)
        scheduled_end = scheduled_start - timedelta(hours=1)  # End antes de start
        
        room_data = JitsiRoomCreate(
            room_type=RoomType.TELECONSULTA,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            title="Test",
        )
        
        with pytest.raises(ValueError, match="Configuração inválida"):
            await room_service.create_room(room_data)
    
    @pytest.mark.asyncio
    async def test_get_room(self, room_service, room_create_data):
        """Testa busca de sala por ID."""
        created_room = await room_service.create_room(room_create_data)
        
        room = await room_service.get_room(created_room.id)
        
        assert room is not None
        assert room.id == created_room.id
        assert room.room_name == created_room.room_name
    
    @pytest.mark.asyncio
    async def test_get_room_not_found(self, room_service):
        """Testa busca de sala inexistente."""
        room = await room_service.get_room(uuid4())
        
        assert room is None
    
    @pytest.mark.asyncio
    async def test_get_room_by_name(self, room_service, room_create_data):
        """Testa busca de sala por nome."""
        created_room = await room_service.create_room(room_create_data)
        
        room = await room_service.get_room_by_name(created_room.room_name)
        
        assert room is not None
        assert room.id == created_room.id
    
    @pytest.mark.asyncio
    async def test_list_rooms(self, room_service, room_create_data):
        """Testa listagem de salas."""
        await room_service.create_room(room_create_data)
        
        rooms = await room_service.list_rooms(limit=10, offset=0)
        
        assert len(rooms) >= 1
    
    @pytest.mark.asyncio
    async def test_list_rooms_by_status(self, room_service, room_create_data):
        """Testa listagem de salas por status."""
        await room_service.create_room(room_create_data)
        
        rooms = await room_service.list_rooms(
            status=RoomStatus.SCHEDULED,
            limit=10,
            offset=0,
        )
        
        assert len(rooms) >= 1
        assert all(room.status == RoomStatus.SCHEDULED for room in rooms)
    
    @pytest.mark.asyncio
    async def test_add_participant(self, room_service, room_create_data):
        """Testa adição de participante."""
        room = await room_service.create_room(room_create_data)
        
        participant_data = JitsiParticipantCreate(
            user_id="user-123",
            user_name="João Silva",
            user_email="joao@test.com",
            role=ParticipantRole.PARTICIPANT,
        )
        
        participant = await room_service.add_participant(
            room_id=room.id,
            participant_data=participant_data,
        )
        
        assert participant.id is not None
        assert participant.room_id == room.id
        assert participant.user_id == "user-123"
        assert participant.user_name == "João Silva"
        assert participant.role == ParticipantRole.PARTICIPANT
        assert participant.jwt_token is not None
    
    @pytest.mark.asyncio
    async def test_remove_participant(self, room_service, room_create_data):
        """Testa remoção de participante."""
        room = await room_service.create_room(room_create_data)
        
        participant_data = JitsiParticipantCreate(
            user_id="user-123",
            user_name="João Silva",
            role=ParticipantRole.PARTICIPANT,
        )
        
        participant = await room_service.add_participant(
            room_id=room.id,
            participant_data=participant_data,
        )
        
        success = await room_service.remove_participant(participant.id)

        assert success is True

    @pytest.mark.asyncio
    async def test_start_room(self, room_service, room_create_data):
        """Testa início de sala."""
        room = await room_service.create_room(room_create_data)

        started_room = await room_service.start_room(room.id)

        assert started_room.status == RoomStatus.ACTIVE
        assert started_room.actual_start is not None

    @pytest.mark.asyncio
    async def test_start_room_already_active(self, room_service, room_create_data):
        """Testa início de sala já ativa."""
        room = await room_service.create_room(room_create_data)
        await room_service.start_room(room.id)

        # Tentar iniciar novamente deve falhar
        with pytest.raises(ValueError, match="já está ativa"):
            await room_service.start_room(room.id)

    @pytest.mark.asyncio
    async def test_end_room(self, room_service, room_create_data):
        """Testa finalização de sala."""
        room = await room_service.create_room(room_create_data)
        await room_service.start_room(room.id)

        ended_room = await room_service.end_room(room.id)

        assert ended_room.status == RoomStatus.COMPLETED
        assert ended_room.actual_end is not None

    @pytest.mark.asyncio
    async def test_end_room_not_active(self, room_service, room_create_data):
        """Testa finalização de sala não ativa."""
        room = await room_service.create_room(room_create_data)

        # Tentar finalizar sala SCHEDULED deve falhar
        with pytest.raises(ValueError, match="não está ativa"):
            await room_service.end_room(room.id)

    @pytest.mark.asyncio
    async def test_cancel_room(self, room_service, room_create_data):
        """Testa cancelamento de sala."""
        room = await room_service.create_room(room_create_data)

        cancelled_room = await room_service.cancel_room(room.id)

        assert cancelled_room.status == RoomStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_room_already_completed(self, room_service, room_create_data):
        """Testa cancelamento de sala já finalizada."""
        room = await room_service.create_room(room_create_data)
        await room_service.start_room(room.id)
        await room_service.end_room(room.id)

        # Tentar cancelar sala COMPLETED deve falhar
        with pytest.raises(ValueError, match="já foi finalizada"):
            await room_service.cancel_room(room.id)

    @pytest.mark.asyncio
    async def test_build_room_response(self, room_service, room_create_data):
        """Testa construção de resposta de sala."""
        room = await room_service.create_room(room_create_data)

        # Adicionar participante
        participant_data = JitsiParticipantCreate(
            user_id="user-123",
            user_name="João Silva",
            role=ParticipantRole.PARTICIPANT,
        )
        await room_service.add_participant(room_id=room.id, participant_data=participant_data)

        response = room_service.build_room_response(room)

        assert response.id == room.id
        assert response.room_name == room.room_name
        assert response.room_url.startswith("https://meet.test.com/")
        assert len(response.participants) == 1
        assert response.participants[0].user_id == "user-123"

