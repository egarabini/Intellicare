"""Testes do cliente WAHA."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from comunicacao.channels.whatsapp.waha_client import WAHAClient


@pytest.fixture
def client() -> WAHAClient:
    return WAHAClient(base_url="http://waha.local:3000", session="default")


def test_to_chat_id() -> None:
    assert WAHAClient._to_chat_id("+55 (11) 99999-9999") == "5511999999999@c.us"


@pytest.mark.asyncio
async def test_send_text_success(client: WAHAClient) -> None:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"messageId": "waha-123"}
    client._client.post = AsyncMock(return_value=response)

    result = await client.send_text(to="+5511999999999", text="Oi")

    assert result["messageId"] == "waha-123"
    client._client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_text_http_error(client: WAHAClient) -> None:
    request = httpx.Request("POST", "http://waha.local:3000/api/sendText")
    response = httpx.Response(500, request=request)
    mocked_response = MagicMock()
    mocked_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "erro",
        request=request,
        response=response,
    )
    client._client.post = AsyncMock(return_value=mocked_response)

    with pytest.raises(httpx.HTTPStatusError):
        await client.send_text(to="+5511999999999", text="Oi")


@pytest.mark.asyncio
async def test_health_check_available(client: WAHAClient) -> None:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"status": "STARTED"}
    client._client.get = AsyncMock(return_value=response)

    health = await client.health_check()

    assert health["available"] is True
    assert health["status"] == "STARTED"


@pytest.mark.asyncio
async def test_health_check_unavailable(client: WAHAClient) -> None:
    client._client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    health = await client.health_check()

    assert health["available"] is False
