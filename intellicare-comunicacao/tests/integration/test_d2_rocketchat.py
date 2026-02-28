"""Testes de integração para D2 - Rocket.Chat Integration."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from comunicacao.bot import IntelliCareBot
from comunicacao.rocketchat import (
    RocketChatChannelService,
    RocketChatClient,
    RocketChatWebhookHandler,
    RCWebhookMessage,
)
from comunicacao.rocketchat.models import RCChannel, RCMessage, RCUser
from comunicacao.sync import UserSyncService
from comunicacao.sync.models import KeycloakEvent, KeycloakUser, UserSyncStatus


class TestRocketChatClient:
    """Testes para RocketChatClient."""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Testa envio de mensagem com sucesso."""
        client = RocketChatClient()
        
        # Mock da resposta da API
        mock_response = {
            "message": {
                "_id": "msg123",
                "rid": "room456",
                "msg": "Test message",
                "ts": "2026-02-17T10:30:00Z",
                "u": {"_id": "user789", "username": "bot"},
            }
        }
        
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.send_message(
                room_id="room456",
                text="Test message",
            )
            
            assert result.id == "msg123"
            assert result.room_id == "room456"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_channel_success(self):
        """Testa criação de canal com sucesso."""
        client = RocketChatClient()
        
        mock_response = {
            "channel": {
                "_id": "channel123",
                "name": "test-channel",
                "t": "c",
                "usernames": ["user1", "user2"],
            }
        }
        
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.create_channel(
                name="test-channel",
                members=["user1", "user2"],
            )
            
            assert result.id == "channel123"
            assert result.name == "test-channel"
            assert result.type == "c"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Testa health check com sucesso."""
        client = RocketChatClient()
        
        mock_response = {"status": "success"}
        
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.health_check()
            
            assert result is True


class TestRocketChatChannelService:
    """Testes para RocketChatChannelService."""
    
    @pytest.mark.asyncio
    async def test_create_case_channel(self):
        """Testa criação de canal de caso."""
        service = RocketChatChannelService()
        
        mock_channel = RCChannel(
            id="channel123",
            name="caso-patient-123",
            type="p",
            usernames=["dr.joao", "enf.ana"],
        )
        
        with patch.object(service.rc_client, "create_private_group", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_channel
            
            result = await service.create_case_channel(
                patient_id="patient-123",
                patient_name="Maria Santos",
                members=["dr.joao", "enf.ana"],
            )
            
            assert result.name == "caso-patient-123"
            assert result.type == "p"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_team_channel(self):
        """Testa criação de canal de equipe."""
        service = RocketChatChannelService()
        
        mock_channel = RCChannel(
            id="channel456",
            name="equipe-ubs-centro",
            type="p",
            usernames=["dr.joao", "dr.maria"],
        )
        
        with patch.object(service.rc_client, "create_private_group", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_channel
            
            result = await service.create_team_channel(
                team_id="ubs-centro",
                team_name="UBS Centro",
                members=["dr.joao", "dr.maria"],
            )
            
            assert result.name == "equipe-ubs-centro"
            assert result.type == "p"
    
    @pytest.mark.asyncio
    async def test_get_or_create_case_channel_existing(self):
        """Testa get_or_create quando canal já existe."""
        service = RocketChatChannelService()
        
        mock_channel = RCChannel(
            id="channel123",
            name="caso-patient-123",
            type="p",
            usernames=["dr.joao"],
        )
        
        with patch.object(service.rc_client, "get_group_info", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_channel
            
            result = await service.get_or_create_case_channel(
                patient_id="patient-123",
                patient_name="Maria Santos",
                members=["dr.joao"],
            )
            
            assert result.id == "channel123"
            mock_get.assert_called_once()


class TestUserSyncService:
    """Testes para UserSyncService."""

    @pytest.mark.asyncio
    async def test_sync_user_new_user(self):
        """Testa sincronização de novo usuário."""
        service = UserSyncService()

        mock_kc_user = KeycloakUser(
            id="kc-user-123",
            username="joao.silva",
            email="joao.silva@example.com",
            first_name="João",
            last_name="Silva",
            enabled=True,
        )

        mock_roles = ["doctor", "user"]

        with patch.object(service.kc_client, "get_user", new_callable=AsyncMock) as mock_get_user, \
             patch.object(service.kc_client, "get_user_roles", new_callable=AsyncMock) as mock_get_roles, \
             patch.object(service.rc_client, "get_user_by_username", new_callable=AsyncMock) as mock_get_rc_user:

            mock_get_user.return_value = mock_kc_user
            mock_get_roles.return_value = mock_roles
            mock_get_rc_user.return_value = None  # Usuário não existe no RC

            result = await service.sync_user("kc-user-123")

            assert result.keycloak_user_id == "kc-user-123"
            assert result.username == "joao.silva"
            assert result.sync_status == UserSyncStatus.SYNCED
            assert "doctor" in result.roles

    @pytest.mark.asyncio
    async def test_sync_user_existing_user(self):
        """Testa sincronização de usuário existente."""
        service = UserSyncService()

        mock_kc_user = KeycloakUser(
            id="kc-user-123",
            username="joao.silva",
            email="joao.silva@example.com",
            first_name="João",
            last_name="Silva",
            enabled=True,
        )

        mock_rc_user = RCUser(
            id="rc-user-456",
            username="joao.silva",
            name="João Silva",
            active=True,
        )

        with patch.object(service.kc_client, "get_user", new_callable=AsyncMock) as mock_get_user, \
             patch.object(service.kc_client, "get_user_roles", new_callable=AsyncMock) as mock_get_roles, \
             patch.object(service.rc_client, "get_user_by_username", new_callable=AsyncMock) as mock_get_rc_user:

            mock_get_user.return_value = mock_kc_user
            mock_get_roles.return_value = ["doctor"]
            mock_get_rc_user.return_value = mock_rc_user

            result = await service.sync_user("kc-user-123")

            assert result.rocketchat_user_id == "rc-user-456"
            assert result.sync_status == UserSyncStatus.SYNCED

    @pytest.mark.asyncio
    async def test_handle_keycloak_event_register(self):
        """Testa processamento de evento REGISTER."""
        service = UserSyncService()

        event = KeycloakEvent(
            type="REGISTER",
            realm_id="bemcuidar",
            user_id="kc-user-123",
            timestamp=1708167000000,
            details={"username": "joao.silva"},
        )

        with patch.object(service, "sync_user", new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = MagicMock(sync_status=UserSyncStatus.SYNCED)

            result = await service.handle_keycloak_event(event)

            assert result is not None
            mock_sync.assert_called_once_with("kc-user-123")

    @pytest.mark.asyncio
    async def test_handle_keycloak_event_delete_disables_user(self):
        """Testa processamento de evento DELETE com desativação no RC."""
        service = UserSyncService()

        event = KeycloakEvent(
            type="DELETE",
            realm_id="bemcuidar",
            user_id="kc-user-123",
            timestamp=1708167000000,
            details={"username": "joao.silva"},
        )

        mock_rc_user = RCUser(
            id="rc-user-456",
            username="joao.silva",
            name="João Silva",
            active=True,
        )

        with patch.object(service.rc_client, "get_user_by_username", new_callable=AsyncMock) as mock_get_rc_user, \
             patch.object(service.rc_client, "set_user_active_status", new_callable=AsyncMock) as mock_set_active:
            mock_get_rc_user.return_value = mock_rc_user
            mock_set_active.return_value = True

            result = await service.handle_keycloak_event(event)

            assert result is not None
            assert result.rocketchat_user_id == "rc-user-456"
            assert result.rc_active is False
            mock_get_rc_user.assert_called_once_with("joao.silva")
            mock_set_active.assert_called_once_with("rc-user-456", False)

    @pytest.mark.asyncio
    async def test_reconcile_all_users(self):
        """Testa reconciliação completa."""
        service = UserSyncService()

        mock_users = [
            KeycloakUser(
                id=f"user-{i}",
                username=f"user{i}",
                email=f"user{i}@example.com",
                enabled=True,
            )
            for i in range(3)
        ]

        with patch.object(service.kc_client, "get_all_users", new_callable=AsyncMock) as mock_get_all, \
             patch.object(service, "sync_user", new_callable=AsyncMock) as mock_sync:

            mock_get_all.return_value = mock_users
            mock_sync.return_value = MagicMock(sync_status=UserSyncStatus.SYNCED)

            stats = await service.reconcile_all_users()

            assert stats["total"] == 3
            assert stats["synced"] == 3
            assert stats["errors"] == 0
            assert mock_sync.call_count == 3


class TestRocketChatWebhookHandler:
    """Testes para RocketChatWebhookHandler."""

    def test_validate_token_success(self):
        """Testa validação de token com sucesso."""
        handler = RocketChatWebhookHandler(webhook_token="secret123")

        result = handler.validate_token("secret123")

        assert result is True

    def test_validate_token_failure(self):
        """Testa validação de token com falha."""
        from comunicacao.rocketchat.webhook_handler import WebhookValidationError

        handler = RocketChatWebhookHandler(webhook_token="secret123")

        with pytest.raises(WebhookValidationError):
            handler.validate_token("wrong_token")

    def test_is_bot_message(self):
        """Testa detecção de mensagem de bot."""
        handler = RocketChatWebhookHandler()

        # Mensagem de bot (flag bot=True)
        message1 = RCWebhookMessage(
            message_id="msg1",
            channel_id="ch1",
            channel_name="test",
            user_id="user1",
            user_name="user",
            text="test",
            timestamp="2026-02-17T10:30:00Z",
            bot=True,
        )

        assert handler.is_bot_message(message1) is True

        # Mensagem de bot (username)
        message2 = RCWebhookMessage(
            message_id="msg2",
            channel_id="ch1",
            channel_name="test",
            user_id="user1",
            user_name="intellicare-bot",
            text="test",
            timestamp="2026-02-17T10:30:00Z",
        )

        assert handler.is_bot_message(message2) is True

        # Mensagem normal
        message3 = RCWebhookMessage(
            message_id="msg3",
            channel_id="ch1",
            channel_name="test",
            user_id="user1",
            user_name="joao.silva",
            text="test",
            timestamp="2026-02-17T10:30:00Z",
        )

        assert handler.is_bot_message(message3) is False

    def test_is_command(self):
        """Testa detecção de comando."""
        handler = RocketChatWebhookHandler()

        assert handler.is_command("/paciente patient-123") is True
        assert handler.is_command("/ajuda") is True
        assert handler.is_command("Olá, como vai?") is False
        assert handler.is_command("") is False

    def test_parse_command(self):
        """Testa parsing de comando."""
        handler = RocketChatWebhookHandler()

        # Comando com argumentos
        command, args = handler.parse_command("/paciente patient-123")
        assert command == "paciente"
        assert args == ["patient-123"]

        # Comando sem argumentos
        command, args = handler.parse_command("/ajuda")
        assert command == "ajuda"
        assert args == []

        # Comando com múltiplos argumentos
        command, args = handler.parse_command("/escalar alert-456 urgente")
        assert command == "escalar"
        assert args == ["alert-456", "urgente"]

    @pytest.mark.asyncio
    async def test_handle_webhook_command(self):
        """Testa processamento de webhook com comando."""
        handler = RocketChatWebhookHandler(webhook_token="secret")

        payload = {
            "_id": "msg123",
            "token": "secret",
            "channel_id": "ch456",
            "channel_name": "alertas-clinicos",
            "user_id": "user789",
            "user_name": "joao.silva",
            "text": "/paciente patient-123",
            "ts": "2026-02-17T10:30:00Z",
        }

        result = await handler.handle_webhook(payload)

        assert result is not None
        assert result["command"] == "paciente"
        assert result["args"] == ["patient-123"]
        assert result["user_name"] == "joao.silva"

    @pytest.mark.asyncio
    async def test_handle_webhook_ignore_bot(self):
        """Testa que webhook ignora mensagens de bot."""
        handler = RocketChatWebhookHandler()

        payload = {
            "_id": "msg123",
            "channel_id": "ch456",
            "channel_name": "test",
            "user_id": "bot",
            "user_name": "intellicare-bot",
            "text": "/paciente patient-123",
            "ts": "2026-02-17T10:30:00Z",
            "bot": True,
        }

        result = await handler.handle_webhook(payload)

        assert result is None


class TestIntelliCareBot:
    """Testes para IntelliCareBot."""

    @pytest.mark.asyncio
    async def test_handle_ajuda(self):
        """Testa comando /ajuda."""
        bot = IntelliCareBot()

        context = {
            "user_name": "joao.silva",
            "channel_id": "ch123",
        }

        response = await bot.handle_ajuda([], context)

        assert "IntelliCare Bot" in response
        assert "/paciente" in response
        assert "/ajuda" in response

    @pytest.mark.asyncio
    async def test_handle_paciente(self):
        """Testa comando /paciente."""
        bot = IntelliCareBot()

        context = {
            "user_name": "joao.silva",
            "channel_id": "ch123",
        }

        # Com argumento
        response = await bot.handle_paciente(["patient-123"], context)

        assert "patient-123" in response
        assert "Informações do Paciente" in response

        # Sem argumento (erro)
        response = await bot.handle_paciente([], context)

        assert "Uso" in response
        assert "/paciente" in response

    @pytest.mark.asyncio
    async def test_handle_lab(self):
        """Testa comando /lab."""
        bot = IntelliCareBot()

        context = {
            "user_name": "joao.silva",
            "channel_id": "ch123",
        }

        response = await bot.handle_lab(["patient-123"], context)

        assert "patient-123" in response
        assert "Resultados de Laboratório" in response
        assert "Glicemia" in response

    @pytest.mark.asyncio
    async def test_handle_alerta(self):
        """Testa comando /alerta."""
        bot = IntelliCareBot()

        context = {
            "user_name": "joao.silva",
            "channel_id": "ch123",
        }

        response = await bot.handle_alerta(["alert-456"], context)

        assert "alert-456" in response
        assert "Detalhes do Alerta" in response

    @pytest.mark.asyncio
    async def test_handle_escalar(self):
        """Testa comando /escalar."""
        bot = IntelliCareBot()

        context = {
            "user_name": "joao.silva",
            "channel_id": "ch123",
        }

        response = await bot.handle_escalar(["alert-456"], context)

        assert "alert-456" in response
        assert "Alerta Escalado" in response
        assert "joao.silva" in response

    @pytest.mark.asyncio
    async def test_handle_teleconsulta(self):
        """Testa comando /teleconsulta."""
        bot = IntelliCareBot()

        context = {
            "user_name": "joao.silva",
            "channel_id": "ch123",
        }

        response = await bot.handle_teleconsulta(["patient-123"], context)

        assert "patient-123" in response
        assert "Sala de Teleconsulta" in response
        assert "meet.gsi.srv.br" in response


class TestAPIEndpoints:
    """Testes para endpoints da API."""

    @pytest.mark.asyncio
    async def test_send_message_endpoint(self):
        """Testa endpoint POST /api/v1/rocketchat/message."""
        # TODO: Implementar teste com TestClient do FastAPI
        pass

    @pytest.mark.asyncio
    async def test_create_channel_endpoint(self):
        """Testa endpoint POST /api/v1/rocketchat/channel."""
        # TODO: Implementar teste com TestClient do FastAPI
        pass

    @pytest.mark.asyncio
    async def test_keycloak_webhook_endpoint(self):
        """Testa endpoint POST /api/v1/sync/keycloak-event."""
        # TODO: Implementar teste com TestClient do FastAPI
        pass

    @pytest.mark.asyncio
    async def test_rocketchat_webhook_endpoint(self):
        """Testa endpoint POST /api/v1/webhooks/rocketchat."""
        # TODO: Implementar teste com TestClient do FastAPI
        pass
