"""Testes para JitsiClient."""

import pytest
from datetime import datetime, timedelta
import jwt

from comunicacao.jitsi.client import JitsiClient
from comunicacao.jitsi.config import JitsiConfig
from comunicacao.jitsi.models import ParticipantRole, RoomType


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


class TestJitsiClient:
    """Testes para JitsiClient."""
    
    def test_generate_room_name(self, jitsi_client):
        """Testa geração de nome de sala."""
        room_name = jitsi_client.generate_room_name(RoomType.TELECONSULTA)
        
        assert room_name.startswith("intellicare-teleconsulta-")
        assert len(room_name) > len("intellicare-teleconsulta-")
    
    def test_generate_room_name_with_id(self, jitsi_client):
        """Testa geração de nome de sala com ID fornecido."""
        room_name = jitsi_client.generate_room_name(RoomType.TELECONSULTA, room_id="abc123")
        
        assert room_name == "intellicare-teleconsulta-abc123"
    
    def test_generate_jwt_token(self, jitsi_client, jitsi_config):
        """Testa geração de token JWT."""
        token = jitsi_client.generate_jwt_token(
            room_name="test-room",
            user_id="user-123",
            user_name="João Silva",
            role=ParticipantRole.PARTICIPANT,
            expires_in_minutes=60,
            user_email="joao@test.com",
        )
        
        # Decodificar token (sem verificar assinatura para teste)
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        assert decoded["iss"] == jitsi_config.app_id
        assert decoded["room"] == "test-room"
        assert decoded["context"]["user"]["id"] == "user-123"
        assert decoded["context"]["user"]["name"] == "João Silva"
        assert decoded["context"]["user"]["email"] == "joao@test.com"
        assert "moderator" not in decoded
    
    def test_generate_jwt_token_moderator(self, jitsi_client):
        """Testa geração de token JWT para moderador."""
        token = jitsi_client.generate_jwt_token(
            room_name="test-room",
            user_id="user-123",
            user_name="Dr. Maria",
            role=ParticipantRole.MODERATOR,
        )
        
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        assert decoded["moderator"] is True
    
    def test_get_room_url(self, jitsi_client):
        """Testa geração de URL de sala."""
        url = jitsi_client.get_room_url("test-room")
        
        assert url == "https://meet.test.com/test-room"
    
    def test_get_room_url_with_token(self, jitsi_client):
        """Testa geração de URL de sala com token."""
        url = jitsi_client.get_room_url("test-room", jwt_token="abc123")
        
        assert url == "https://meet.test.com/test-room?jwt=abc123"
    
    def test_validate_room_config_valid(self, jitsi_client):
        """Testa validação de configuração válida."""
        scheduled_start = datetime.utcnow() + timedelta(hours=1)
        scheduled_end = scheduled_start + timedelta(hours=1)
        
        errors = jitsi_client.validate_room_config(
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            max_participants=5,
        )
        
        assert errors == []
    
    def test_validate_room_config_start_after_end(self, jitsi_client):
        """Testa validação com start após end."""
        scheduled_start = datetime.utcnow() + timedelta(hours=2)
        scheduled_end = scheduled_start - timedelta(hours=1)
        
        errors = jitsi_client.validate_room_config(
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            max_participants=5,
        )
        
        assert len(errors) > 0
        assert any("anterior" in error for error in errors)
    
    def test_validate_room_config_past_start(self, jitsi_client):
        """Testa validação com start no passado."""
        scheduled_start = datetime.utcnow() - timedelta(hours=1)
        scheduled_end = scheduled_start + timedelta(hours=1)
        
        errors = jitsi_client.validate_room_config(
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            max_participants=5,
        )
        
        assert len(errors) > 0
        assert any("passado" in error for error in errors)
    
    def test_validate_room_config_too_long(self, jitsi_client):
        """Testa validação com duração muito longa."""
        scheduled_start = datetime.utcnow() + timedelta(hours=1)
        scheduled_end = scheduled_start + timedelta(hours=10)
        
        errors = jitsi_client.validate_room_config(
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            max_participants=5,
        )
        
        assert len(errors) > 0
        assert any("8 horas" in error for error in errors)
    
    def test_validate_room_config_too_short(self, jitsi_client):
        """Testa validação com duração muito curta."""
        scheduled_start = datetime.utcnow() + timedelta(hours=1)
        scheduled_end = scheduled_start + timedelta(minutes=2)
        
        errors = jitsi_client.validate_room_config(
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            max_participants=5,
        )
        
        assert len(errors) > 0
        assert any("5 minutos" in error for error in errors)
    
    def test_validate_room_config_too_many_participants(self, jitsi_client):
        """Testa validação com muitos participantes."""
        scheduled_start = datetime.utcnow() + timedelta(hours=1)
        scheduled_end = scheduled_start + timedelta(hours=1)
        
        errors = jitsi_client.validate_room_config(
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            max_participants=100,
        )
        
        assert len(errors) > 0
        assert any("exceder" in error for error in errors)

