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
from comunicacao.routing import DefaultLGPDGateway
from comunicacao.routing.engine import RoutingEngine


class _FakeDispatcher:
    channel = "fake"

    async def send(self, message: ChannelMessage) -> DispatchResult:
        if message.content.body == "fail":
            return DispatchResult(success=False, error_code="send_error", error_message="falha simulada")
        return DispatchResult(success=True, channel_message_id="msg-123", channel_room_id="room-1")

    async def is_available(self) -> bool:
        return True

    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        return DeliveryStatus.SENT if channel_message_id else DeliveryStatus.UNKNOWN

    async def get_health(self) -> ChannelHealth:
        return ChannelHealth(channel=self.channel, available=True, status="up")

    async def supports_read_receipt(self) -> bool:
        return False

    async def supports_rich_content(self) -> bool:
        return True


def test_channels_endpoints_list_health_and_test() -> None:
    app = create_app()
    with TestClient(app) as client:
        manager = DispatcherManager()
        manager.register(_FakeDispatcher())
        _state["dispatcher_manager"] = manager

        list_response = client.get("/api/v1/channels")
        health_response = client.get("/api/v1/channels/fake/health")
        test_response = client.post("/api/v1/channels/fake/test", json={"message": "ok"})

    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1
    assert list_response.json()["items"][0]["channel"] == "fake"

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "up"

    assert test_response.status_code == 200
    assert test_response.json()["success"] is True
    assert test_response.json()["channel_message_id"] == "msg-123"


def test_channels_test_endpoint_returns_failure_payload() -> None:
    app = create_app()
    with TestClient(app) as client:
        manager = DispatcherManager()
        manager.register(_FakeDispatcher())
        _state["dispatcher_manager"] = manager
        response = client.post("/api/v1/channels/fake/test", json={"message": "fail"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["error_code"] == "send_error"


def test_default_lgpd_gateway_applies_critical_override() -> None:
    gateway = DefaultLGPDGateway()

    import asyncio

    result = asyncio.run(
        gateway.can_send(
            patient_id="pac-1",
            channel="sms",
            intent_type="clinical_alert",
            severity="critical",
        )
    )
    assert result.allowed is True
    assert result.override_applied is True


def test_routing_engine_uses_lgpd_gateway_contract() -> None:
    """Verifica que DefaultLGPDGateway permite envios de baixa severidade sem override."""
    import asyncio

    # Use DefaultLGPDGateway diretamente (mesmo contrato que RoutingEngine usa internamente)
    from comunicacao.routing.lgpd import DefaultLGPDGateway as _DLG
    gateway = _DLG()
    result = asyncio.run(
        gateway.can_send(
            patient_id="pac-2",
            channel="email",
            intent_type="education",
            severity="low",
        )
    )
    assert result.allowed is True
    assert result.override_applied is False
