"""Tests for WandaBotHandler (EF-W012)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from wanda.bot.handler import WandaBotHandler
from wanda.bot.models import BotCommand, AuthResult, ParsedCommand, RCMessage


def make_payload(**kwargs):
    defaults = {
        "token": "valid-token",
        "channel_id": "GENERAL",
        "channel_name": "general",
        "user_id": "user-1",
        "user_name": "nurse1",
        "text": "@intellicare /ajuda",
        "trigger_word": "@intellicare",
    }
    defaults.update(kwargs)
    return defaults


@pytest.fixture
def mock_rc_client():
    client = AsyncMock()
    client.send = AsyncMock(return_value=True)
    client.send_text = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_router():
    router = MagicMock()
    router.route = AsyncMock(return_value=("Ajuda disponível", []))
    return router


@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.authorize = AsyncMock(return_value=AuthResult(authorized=True))
    return auth


@pytest.fixture
def handler(mock_rc_client, mock_router, mock_auth):
    return WandaBotHandler(
        webhook_token="valid-token",
        bot_user_id="bot-user-id",
        rc_client=mock_rc_client,
        router=mock_router,
        auth=mock_auth,
    )


class TestWandaBotHandler:
    @pytest.mark.asyncio
    async def test_invalid_token_returns_unauthorized(self, handler):
        payload = make_payload(token="wrong-token")
        result = await handler.handle_webhook(payload)
        assert result["status"] == "unauthorized"

    @pytest.mark.asyncio
    async def test_self_message_ignored(self, handler):
        payload = make_payload(user_id="bot-user-id")
        result = await handler.handle_webhook(payload)
        assert result["status"] == "ignored"
        assert "self-message" in result["reason"]

    @pytest.mark.asyncio
    async def test_no_trigger_ignored(self, handler):
        payload = make_payload(text="plain text with no trigger")
        result = await handler.handle_webhook(payload)
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_ajuda_command_processed(self, handler, mock_router):
        payload = make_payload(text="@intellicare /ajuda")
        result = await handler.handle_webhook(payload)
        assert result["status"] == "ok"
        assert result["command"] == "ajuda"
        mock_router.route.assert_called_once()

    @pytest.mark.asyncio
    async def test_unauthorized_command_blocked(self, mock_rc_client, mock_router, mock_auth):
        mock_auth.authorize = AsyncMock(
            return_value=AuthResult(authorized=False, reason="Sem permissão")
        )
        handler = WandaBotHandler(
            webhook_token="",
            rc_client=mock_rc_client,
            router=mock_router,
            auth=mock_auth,
        )
        payload = make_payload(token="", text="@intellicare /status")
        result = await handler.handle_webhook(payload)
        assert result["status"] == "unauthorized"
        mock_rc_client.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_routing_error_handled(self, handler, mock_router):
        mock_router.route.side_effect = Exception("routing error")
        payload = make_payload()
        result = await handler.handle_webhook(payload)
        assert result["status"] == "ok"  # still responds
        handler._rc_client.send.assert_called()

    @pytest.mark.asyncio
    async def test_context_updated_with_patient_id(self, handler):
        payload = make_payload(text="@intellicare /paciente patient-123")
        await handler.handle_webhook(payload)
        # Patient ID should be stored in context
        ctx = await handler._context.get("default", "user-1", "GENERAL")
        assert ctx.get("patient_id") == "patient-123"

    @pytest.mark.asyncio
    async def test_command_log_updated(self, handler):
        payload = make_payload()
        await handler.handle_webhook(payload)
        assert len(handler.recent_commands) >= 1
        assert handler.recent_commands[0]["command"] == "ajuda"

    @pytest.mark.asyncio
    async def test_metrics_tracks_commands(self, handler):
        payload = make_payload()
        await handler.handle_webhook(payload)
        metrics = handler.metrics
        assert metrics["total"] >= 1
        assert "ajuda" in metrics["by_command"]

    @pytest.mark.asyncio
    async def test_no_token_validation_when_empty(self, mock_rc_client, mock_router, mock_auth):
        handler = WandaBotHandler(
            webhook_token="",  # no token validation
            rc_client=mock_rc_client,
            router=mock_router,
            auth=mock_auth,
        )
        payload = make_payload(token="anything")
        result = await handler.handle_webhook(payload)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_invalid_command_sends_error_text(self, handler, mock_rc_client):
        """Covers bot/handler.py:80 — send_text when parse error != 'sem trigger'."""
        bad_parsed = ParsedCommand(
            command=None,
            is_valid=False,
            error="comando desconhecido",
        )
        with patch.object(handler._parser, "parse", return_value=bad_parsed):
            payload = make_payload(text="@intellicare /naoexiste")
            result = await handler.handle_webhook(payload)
        assert result["status"] == "ignored"
        mock_rc_client.send_text.assert_awaited_once()
        call_args = mock_rc_client.send_text.call_args[0]
        assert "comando desconhecido" in call_args[1]

    @pytest.mark.asyncio
    async def test_command_log_trimmed_when_over_500(self, handler):
        """Covers bot/handler.py:124 — trim log when > 500 entries."""
        # Pre-fill log with 501 fake entries
        handler._command_log = [
            {"ts": "t", "user": "u", "command": "ajuda", "patient_id": None}
        ] * 501
        payload = make_payload(text="@intellicare /ajuda")
        await handler.handle_webhook(payload)
        # After trim: log should be <= 200 + 1 (the new entry)
        assert len(handler._command_log) <= 201
