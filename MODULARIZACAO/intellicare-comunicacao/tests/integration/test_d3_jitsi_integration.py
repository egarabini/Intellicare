"""Testes de integração D3 (Jitsi) ↔ D1 (Routing Engine)."""

import pytest
from datetime import datetime, timedelta

from comunicacao.jitsi.dispatcher import JitsiDispatcher
from comunicacao.jitsi.config import JitsiConfig
from comunicacao.dispatchers import DispatcherManager
from comunicacao.routing.models import (
    ChannelMessage,
    ResolvedRecipient,
    RenderedContent,
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
async def dispatcher_manager(async_db_session, jitsi_config):
    """Fixture de DispatcherManager com JitsiDispatcher registrado."""
    manager = DispatcherManager()
    
    jitsi_dispatcher = JitsiDispatcher(db=async_db_session, config=jitsi_config)
    manager.register(jitsi_dispatcher)
    
    return manager


class TestD3JitsiIntegration:
    """Testes de integração D3 ↔ D1."""
    
    @pytest.mark.asyncio
    async def test_dispatcher_manager_has_jitsi(self, dispatcher_manager):
        """Testa que DispatcherManager tem dispatcher Jitsi."""
        dispatcher = dispatcher_manager.get_dispatcher("jitsi")
        
        assert dispatcher is not None
        assert isinstance(dispatcher, JitsiDispatcher)
    
    @pytest.mark.asyncio
    async def test_dispatch_via_manager(self, dispatcher_manager):
        """Testa dispatch via DispatcherManager."""
        scheduled_start = datetime.utcnow() + timedelta(hours=1)
        scheduled_end = scheduled_start + timedelta(hours=1)
        
        message = ChannelMessage(
            intent_id="intent-123",
            correlation_id="corr-456",
            channel="jitsi",
            recipient=ResolvedRecipient(
                recipient_id="patient-789",
                recipient_type="patient",
                metadata={"name": "João Silva"},
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
        
        result = await dispatcher_manager.dispatch("jitsi", message)
        
        assert result.success is True
        assert result.metadata is not None
        assert "room_url" in result.metadata
        assert "jwt_token" in result.metadata
    
    @pytest.mark.asyncio
    async def test_full_flow_create_room_add_participants(self, dispatcher_manager):
        """Testa fluxo completo: criar sala + adicionar múltiplos participantes."""
        scheduled_start = datetime.utcnow() + timedelta(hours=1)
        scheduled_end = scheduled_start + timedelta(hours=1)
        
        # 1. Criar sala com primeiro participante (moderador)
        message1 = ChannelMessage(
            intent_id="intent-123",
            correlation_id="corr-456",
            channel="jitsi",
            recipient=ResolvedRecipient(
                recipient_id="doctor-001",
                recipient_type="professional",
                metadata={"name": "Dr. Maria Silva"},
            ),
            content=RenderedContent(
                format="markdown",
                body="Sala de teleconsulta criada",
                title="Teleconsulta - Cardiologia",
            ),
            metadata={
                "room_type": "teleconsulta",
                "scheduled_start": scheduled_start.isoformat(),
                "scheduled_end": scheduled_end.isoformat(),
                "patient_id": "patient-789",
                "role": "moderator",
            },
        )
        
        result1 = await dispatcher_manager.dispatch("jitsi", message1)
        
        assert result1.success is True
        room_id = result1.metadata["room_id"]
        
        # 2. Adicionar segundo participante (paciente) à mesma sala
        message2 = ChannelMessage(
            intent_id="intent-124",
            correlation_id="corr-457",
            channel="jitsi",
            recipient=ResolvedRecipient(
                recipient_id="patient-789",
                recipient_type="patient",
                metadata={"name": "João Silva"},
            ),
            content=RenderedContent(
                format="markdown",
                body="Convite para teleconsulta",
                title="Teleconsulta - Dr. Maria",
            ),
            metadata={
                "room_id": room_id,  # Usar sala existente
                "role": "participant",
            },
        )
        
        result2 = await dispatcher_manager.dispatch("jitsi", message2)
        
        assert result2.success is True
        assert result2.metadata["room_id"] == room_id
        
        # 3. Verificar que ambos têm URLs diferentes (tokens diferentes)
        assert result1.metadata["room_url"] != result2.metadata["room_url"]
        assert result1.metadata["jwt_token"] != result2.metadata["jwt_token"]
    
    @pytest.mark.asyncio
    async def test_health_check_via_manager(self, dispatcher_manager):
        """Testa health check via DispatcherManager."""
        dispatcher = dispatcher_manager.get_dispatcher("jitsi")
        health = await dispatcher.health_check()
        
        assert health.is_healthy is True
        assert health.channel_name == "jitsi"
    
    @pytest.mark.asyncio
    async def test_capabilities_via_manager(self, dispatcher_manager):
        """Testa capabilities via DispatcherManager."""
        dispatcher = dispatcher_manager.get_dispatcher("jitsi")
        capabilities = await dispatcher.get_capabilities()
        
        assert capabilities.supports_read_receipt is True
        assert capabilities.supports_rich_content is True
        assert capabilities.supports_interactive is True

