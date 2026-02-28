from __future__ import annotations

from fastapi.testclient import TestClient

from comunicacao.api.app import _state, create_app
from comunicacao.dispatchers import (
    ChannelHealth,
    ChannelMessage,
    DeliveryStatus,
    DispatchResult,
    DispatcherManager,
)


class _FakeRocketchatDispatcher:
    """Fake dispatcher para testes."""

    channel = "rocketchat"

    async def send(self, message: ChannelMessage) -> DispatchResult:
        return DispatchResult(
            success=True,
            channel_message_id="rc-msg-123",
            channel_room_id="rc-room-456",
        )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        return DeliveryStatus.DELIVERED

    async def cancel(self, channel_message_id: str) -> bool:
        return True

    async def health_check(self) -> ChannelHealth:
        return ChannelHealth(
            channel="rocketchat",
            available=True,
            status="healthy",
            details={"version": "7.13.2", "connected": True},
        )

    async def test_send(self, recipient_id: str, message: str) -> DispatchResult:
        return DispatchResult(
            success=True,
            channel_message_id="test-msg-123",
        )

    async def is_available(self) -> bool:
        return True

    async def supports_read_receipt(self) -> bool:
        return True

    async def supports_rich_content(self) -> bool:
        return True

    def get_capabilities(self) -> dict:
        return {
            "read_receipt": True,
            "rich_content": True,
            "attachments": True,
        }

    def validate_recipient(self, recipient_id: str) -> tuple[bool, str | None]:
        return (True, None)


class _FakeEmailDispatcher:
    """Fake email dispatcher para testes."""

    channel = "email"

    async def send(self, message: ChannelMessage) -> DispatchResult:
        return DispatchResult(
            success=True,
            channel_message_id="email-msg-789",
        )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        return DeliveryStatus.DELIVERED

    async def cancel(self, channel_message_id: str) -> bool:
        return False

    async def health_check(self) -> ChannelHealth:
        return ChannelHealth(
            channel="email",
            available=True,
            status="healthy",
            details={"smtp_connected": True},
        )

    async def test_send(self, recipient_id: str, message: str) -> DispatchResult:
        return DispatchResult(
            success=True,
            channel_message_id="test-email-456",
        )

    async def is_available(self) -> bool:
        return True

    async def supports_read_receipt(self) -> bool:
        return False

    async def supports_rich_content(self) -> bool:
        return True

    def get_capabilities(self) -> dict:
        return {
            "read_receipt": False,
            "rich_content": True,
            "attachments": True,
        }

    def validate_recipient(self, recipient_id: str) -> tuple[bool, str | None]:
        if "@" not in recipient_id:
            return (False, "Email inválido")
        return (True, None)


def _override_dispatcher_manager() -> None:
    """Sobrescreve o dispatcher manager com fakes."""
    manager = DispatcherManager()
    manager.register(_FakeRocketchatDispatcher())
    manager.register(_FakeEmailDispatcher())
    _state["dispatcher_manager"] = manager


def test_list_channels_returns_all_registered() -> None:
    """Testa que listar canais retorna todos os registrados."""
    app = create_app()
    with TestClient(app) as client:
        _override_dispatcher_manager()
        response = client.get("/api/v1/channels")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["count"] == 2
    assert len(data["items"]) == 2
    channels = [item["channel"] for item in data["items"]]
    assert "rocketchat" in channels
    assert "email" in channels


def test_list_channels_shows_capabilities() -> None:
    """Testa que listar canais mostra as capacidades de cada um."""
    app = create_app()
    with TestClient(app) as client:
        _override_dispatcher_manager()
        response = client.get("/api/v1/channels")

    assert response.status_code == 200
    data = response.json()
    rocketchat = next(item for item in data["items"] if item["channel"] == "rocketchat")
    email = next(item for item in data["items"] if item["channel"] == "email")

    assert rocketchat["available"] is True
    assert rocketchat["supports_read_receipt"] is True
    assert rocketchat["supports_rich_content"] is True

    assert email["available"] is True
    assert email["supports_read_receipt"] is False
    assert email["supports_rich_content"] is True


def test_channel_health_returns_status() -> None:
    """Testa que health check retorna status do canal."""
    app = create_app()
    with TestClient(app) as client:
        _override_dispatcher_manager()
        response = client.get("/api/v1/channels/rocketchat/health")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["channel"] == "rocketchat"
    assert data["available"] is True
    assert data["status"] == "healthy"
    assert "details" in data
    assert data["details"]["version"] == "7.13.2"
    assert data["details"]["connected"] is True


def test_channel_health_for_email() -> None:
    """Testa health check para canal de email."""
    app = create_app()
    with TestClient(app) as client:
        _override_dispatcher_manager()
        response = client.get("/api/v1/channels/email/health")

    assert response.status_code == 200
    data = response.json()
    assert data["channel"] == "email"
    assert data["available"] is True
    assert data["details"]["smtp_connected"] is True


def test_channel_health_not_found_returns_404() -> None:
    """Testa que health check de canal inexistente retorna 404."""
    app = create_app()
    with TestClient(app) as client:
        _override_dispatcher_manager()
        response = client.get("/api/v1/channels/nonexistent/health")

    assert response.status_code == 404


def test_channel_test_sends_message() -> None:
    """Testa que endpoint de teste envia mensagem."""
    app = create_app()
    with TestClient(app) as client:
        _override_dispatcher_manager()
        response = client.post(
            "/api/v1/channels/rocketchat/test",
            json={
                "recipient_id": "test-user-123",
                "room_id": "test-room-456",
                "message": "Mensagem de teste",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["channel"] == "rocketchat"
    assert data["success"] is True
    assert data["channel_message_id"] is not None


def test_channel_test_with_default_message() -> None:
    """Testa endpoint de teste com mensagem padrão."""
    app = create_app()
    with TestClient(app) as client:
        _override_dispatcher_manager()
        response = client.post(
            "/api/v1/channels/email/test",
            json={"recipient_id": "test@example.com"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["channel"] == "email"


def test_channel_test_not_found_returns_404() -> None:
    """Testa que teste de canal inexistente retorna 404."""
    app = create_app()
    with TestClient(app) as client:
        _override_dispatcher_manager()
        response = client.post(
            "/api/v1/channels/nonexistent/test",
            json={"recipient_id": "test-user"},
        )

    assert response.status_code == 404


def test_list_channels_when_no_manager_returns_empty() -> None:
    """Testa que listar canais sem manager retorna lista vazia."""
    app = create_app()
    with TestClient(app) as client:
        _state["dispatcher_manager"] = None
        response = client.get("/api/v1/channels")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["count"] == 0
    assert len(data["items"]) == 0

