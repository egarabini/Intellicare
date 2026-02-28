"""Testes para JitsiDispatcher."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from comunicacao.jitsi.dispatcher import JitsiDispatcher
from comunicacao.jitsi.config import JitsiConfig
from comunicacao.jitsi.models import RoomType, RoomStatus, ParticipantRole
from comunicacao.routing.models import (
    ChannelMessage,
    ResolvedRecipient,
    RenderedContent,
    DeliveryStatus,
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
async def jitsi_dispatcher(async_db_session, jitsi_config):
    """Fixture de JitsiDispatcher."""
    return JitsiDispatcher(db=async_db_session, config=jitsi_config)


@pytest.fixture
def channel_message():
    """Fixture de ChannelMessage."""
    scheduled_start = datetime.utcnow() + timedelta(hours=1)
    scheduled_end = scheduled_start + timedelta(hours=1)
    
    return ChannelMessage(
        intent_id="intent-123",
        correlation_id="corr-456",
        channel="jitsi",
        recipient=ResolvedRecipient(
            recipient_id="patient-789",
            recipient_type="patient",
            metadata={"name": "João Silva", "email": "joao@test.com"},
        ),
        content=RenderedContent(
            format="markdown",
            body="Convite para teleconsulta",
            title="Teleconsulta - Dr. Maria",
        ),
        metadata={
            "room_type": "teleconsulta",
            "scheduled_start": scheduled_start.isoformat(),
            "scheduled_end": scheduled_end.isoformat(),
            "patient_id": "patient-789",
            "role": "participant",
        },
    )


class TestJitsiDispatcher:
    """Testes para JitsiDispatcher."""
    
    @pytest.mark.asyncio
    async def test_send_creates_room(self, jitsi_dispatcher, channel_message):
        """Testa que send() cria sala."""
        result = await jitsi_dispatcher.send(channel_message)
        
        assert result.success is True
        assert result.channel_message_id is not None
        assert result.metadata is not None
        assert "room_id" in result.metadata
        assert "room_url" in result.metadata
        assert "jwt_token" in result.metadata
    
    @pytest.mark.asyncio
    async def test_send_with_existing_room(self, jitsi_dispatcher, channel_message):
        """Testa que send() usa sala existente se room_id fornecido."""
        # Criar sala primeiro
        first_result = await jitsi_dispatcher.send(channel_message)
        room_id = first_result.metadata["room_id"]
        
        # Enviar novamente com room_id
        channel_message.metadata["room_id"] = room_id
        second_result = await jitsi_dispatcher.send(channel_message)
        
        assert second_result.success is True
        assert second_result.metadata["room_id"] == room_id
    
    @pytest.mark.asyncio
    async def test_send_moderator_role(self, jitsi_dispatcher, channel_message):
        """Testa envio com role=moderator."""
        channel_message.metadata["role"] = "moderator"
        
        result = await jitsi_dispatcher.send(channel_message)
        
        assert result.success is True
        assert result.metadata["role"] == "moderator"
    
    @pytest.mark.asyncio
    async def test_get_status_sent(self, jitsi_dispatcher, channel_message):
        """Testa get_status() para participante que não entrou."""
        result = await jitsi_dispatcher.send(channel_message)
        participant_id = result.channel_message_id
        
        status = await jitsi_dispatcher.get_status(participant_id)
        
        assert status == DeliveryStatus.SENT
    
    @pytest.mark.asyncio
    async def test_get_status_unknown(self, jitsi_dispatcher):
        """Testa get_status() para participante inexistente."""
        status = await jitsi_dispatcher.get_status(str(uuid4()))
        
        assert status == DeliveryStatus.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_cancel(self, jitsi_dispatcher, channel_message):
        """Testa cancel() remove participante."""
        result = await jitsi_dispatcher.send(channel_message)
        participant_id = result.channel_message_id
        
        success = await jitsi_dispatcher.cancel(participant_id)
        
        assert success is True
        
        # Verificar que status agora é UNKNOWN
        status = await jitsi_dispatcher.get_status(participant_id)
        assert status == DeliveryStatus.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_cancel_not_found(self, jitsi_dispatcher):
        """Testa cancel() para participante inexistente."""
        success = await jitsi_dispatcher.cancel(str(uuid4()))
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_health_check(self, jitsi_dispatcher):
        """Testa health_check()."""
        health = await jitsi_dispatcher.health_check()
        
        assert health.is_healthy is True
        assert health.channel_name == "jitsi"
    
    @pytest.mark.asyncio
    async def test_test_send(self, jitsi_dispatcher):
        """Testa test_send()."""
        recipient = ResolvedRecipient(
            recipient_id="test-user",
            recipient_type="patient",
            metadata={"name": "Test User"},
        )
        
        result = await jitsi_dispatcher.test_send(recipient)
        
        assert result.success is True
        assert result.metadata is not None
        assert "room_url" in result.metadata
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, jitsi_dispatcher):
        """Testa get_capabilities()."""
        capabilities = await jitsi_dispatcher.get_capabilities()
        
        assert capabilities.supports_read_receipt is True
        assert capabilities.supports_rich_content is True
        assert capabilities.supports_attachments is False
        assert capabilities.supports_interactive is True
    
    @pytest.mark.asyncio
    async def test_validate_recipient(self, jitsi_dispatcher):
        """Testa validate_recipient()."""
        recipient = ResolvedRecipient(
            recipient_id="user-123",
            recipient_type="patient",
        )
        
        validation = await jitsi_dispatcher.validate_recipient(recipient)
        
        assert validation.is_valid is True

