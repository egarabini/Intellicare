"""Testes de backend WAHA no WhatsAppDispatcher."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from comunicacao.channels.whatsapp.config import WhatsAppConfig
from comunicacao.channels.whatsapp.dispatcher import WhatsAppDispatcher
from comunicacao.channels.whatsapp.waha_config import WAHAConfig
from comunicacao.dispatchers.base import ChannelMessage, RenderedContent, ResolvedRecipient


@pytest.fixture
def whatsapp_config() -> WhatsAppConfig:
    return WhatsAppConfig(
        phone_number_id="123456789",
        business_account_id="987654321",
        access_token="test-token",
        webhook_verify_token="test-verify-token",
        enabled=True,
    )


@pytest.fixture
def waha_config() -> WAHAConfig:
    return WAHAConfig(base_url="http://waha.local:3000", session="default")


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


def _message(with_template: bool = False) -> ChannelMessage:
    metadata = {}
    if with_template:
        metadata = {"template_name": "alerta_clinico", "template_params": ["a", "b"]}
    return ChannelMessage(
        intent_id="intent-1",
        correlation_id="corr-1",
        channel="whatsapp",
        recipient=ResolvedRecipient(recipient_id="+5511999999999", recipient_type="phone"),
        content=RenderedContent(format="text", body="Mensagem WAHA de teste", subject=None),
        metadata=metadata,
    )


@pytest.mark.asyncio
async def test_dispatcher_send_waha_backend(
    whatsapp_config: WhatsAppConfig,
    waha_config: WAHAConfig,
    mock_db: AsyncMock,
) -> None:
    dispatcher = WhatsAppDispatcher(
        db=mock_db,
        config=whatsapp_config,
        backend="waha",
        waha_config=waha_config,
    )
    dispatcher._client_waha.send_text = AsyncMock(return_value={"messageId": "waha-1"})  # type: ignore[union-attr]

    result = await dispatcher.send(_message())

    assert result.success is True
    assert result.channel_message_id == "waha-1"
    assert result.metadata["provider"] == "waha"


@pytest.mark.asyncio
async def test_dispatcher_fallback_auto(
    whatsapp_config: WhatsAppConfig,
    waha_config: WAHAConfig,
    mock_db: AsyncMock,
) -> None:
    dispatcher = WhatsAppDispatcher(
        db=mock_db,
        config=whatsapp_config,
        backend="auto",
        waha_config=waha_config,
    )
    dispatcher._client_meta.send_template_message = AsyncMock(side_effect=Exception("meta down"))  # type: ignore[union-attr]
    dispatcher._client_waha.send_text = AsyncMock(return_value={"messageId": "waha-fallback"})  # type: ignore[union-attr]

    result = await dispatcher.send(_message(with_template=True))

    assert result.success is True
    assert result.channel_message_id == "waha-fallback"
    assert result.metadata["provider"] == "waha"
    assert result.metadata["fallback_from"] == "meta"


@pytest.mark.asyncio
async def test_dispatcher_meta_priority_auto(
    whatsapp_config: WhatsAppConfig,
    waha_config: WAHAConfig,
    mock_db: AsyncMock,
) -> None:
    dispatcher = WhatsAppDispatcher(
        db=mock_db,
        config=whatsapp_config,
        backend="auto",
        waha_config=waha_config,
    )
    dispatcher._client_meta.send_template_message = AsyncMock(  # type: ignore[union-attr]
        return_value={"messages": [{"id": "meta-1"}]}
    )
    dispatcher._client_waha.send_text = AsyncMock(return_value={"messageId": "waha-should-not-run"})  # type: ignore[union-attr]

    result = await dispatcher.send(_message(with_template=True))

    assert result.success is True
    assert result.channel_message_id == "meta-1"
    assert result.metadata["provider"] == "meta"
    dispatcher._client_waha.send_text.assert_not_called()  # type: ignore[union-attr]
