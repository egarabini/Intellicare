"""Testes do WAHAWebhookHandler — 12 cenários."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from comunicacao.channels.whatsapp.waha_webhook_handler import (
    WAHAWebhookHandler,
    _extract_phone,
    _REDIS_STREAM,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_handler(redis_url: str | None = None) -> tuple[WAHAWebhookHandler, MagicMock]:
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    handler = WAHAWebhookHandler(db=db, redis_url=redis_url)
    return handler, db


def _message_payload(
    body: str = "Oi",
    from_chat_id: str = "5511999999999@c.us",
    msg_id: str = "msg-001",
    from_me: bool = False,
) -> dict:
    return {
        "event": "message",
        "session": "default",
        "payload": {
            "id": msg_id,
            "from": from_chat_id,
            "to": "5511000000000@c.us",
            "body": body,
            "type": "chat",
            "timestamp": 1700000000,
            "fromMe": from_me,
        },
    }


# ── _extract_phone ─────────────────────────────────────────────────────────────


def test_extract_phone_strips_at_suffix() -> None:
    assert _extract_phone("5511999999999@c.us") == "+5511999999999"


def test_extract_phone_preserves_plus() -> None:
    assert _extract_phone("+5511999999999@c.us") == "+5511999999999"


def test_extract_phone_no_suffix() -> None:
    assert _extract_phone("5511999999999") == "+5511999999999"


# ── handle_event dispatch ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_event_routes_message() -> None:
    handler, db = _make_handler()
    handler._handle_incoming_message = AsyncMock()
    payload = _message_payload()
    await handler.handle_event(payload)
    handler._handle_incoming_message.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_handle_event_ignores_unknown_events() -> None:
    handler, _ = _make_handler()
    handler._handle_incoming_message = AsyncMock()
    await handler.handle_event({"event": "ack", "session": "default"})
    handler._handle_incoming_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_event_session_status_does_not_raise() -> None:
    handler, _ = _make_handler()
    await handler.handle_event({
        "event": "session.status",
        "session": "default",
        "payload": {"status": "STOPPED"},
    })  # deve logar e retornar sem erro


# ── Incoming message ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_incoming_message_persists_to_db() -> None:
    handler, db = _make_handler()
    await handler.handle_event(_message_payload(body="Tomei o remédio"))
    db.add.assert_called_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_incoming_message_sets_inbound_direction() -> None:
    handler, db = _make_handler()
    await handler.handle_event(_message_payload())
    log = db.add.call_args[0][0]
    assert log.direction == "inbound"
    assert log.channel == "whatsapp"


@pytest.mark.asyncio
async def test_incoming_message_provider_waha_in_provider_status() -> None:
    handler, db = _make_handler()
    await handler.handle_event(_message_payload())
    log = db.add.call_args[0][0]
    assert log.provider_status is not None
    assert "waha" in log.provider_status


@pytest.mark.asyncio
async def test_from_me_message_ignored() -> None:
    """Mensagens enviadas por nós (fromMe=True) devem ser ignoradas."""
    handler, db = _make_handler()
    await handler.handle_event(_message_payload(from_me=True))
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_missing_from_field_ignored() -> None:
    """Evento sem remetente deve ser ignorado sem erro."""
    handler, db = _make_handler()
    await handler.handle_event({
        "event": "message",
        "session": "default",
        "payload": {"id": "x", "body": "..."},
    })
    db.add.assert_not_called()


# ── Redis publishing ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_redis_event_published_when_configured() -> None:
    handler, _ = _make_handler(redis_url="redis://localhost:6379")
    mock_redis = AsyncMock()
    mock_redis.xadd = AsyncMock()
    handler._redis = mock_redis

    await handler.handle_event(_message_payload(body="Consulta confirmada"))

    mock_redis.xadd.assert_awaited_once()
    call_args = mock_redis.xadd.call_args
    assert call_args[0][0] == _REDIS_STREAM
    event_fields = call_args[0][1]
    assert event_fields["source"] == "waha"
    assert "+5511999999999" in event_fields["from_phone"]


@pytest.mark.asyncio
async def test_redis_not_called_when_no_url() -> None:
    handler, _ = _make_handler(redis_url=None)
    # _get_redis deve retornar None sem configurar _redis
    redis_client = await handler._get_redis()
    assert redis_client is None
