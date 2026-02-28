"""
Testes para PushDispatcher (D4).

Testa envio de push notifications via VAPID e FCM.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from comunicacao.channels.models import PushSubscription
from comunicacao.channels.push.config import PushConfig, VAPIDConfig
from comunicacao.channels.push.dispatcher import PushDispatcher
from comunicacao.dispatchers.base import (
    ChannelMessage,
    RenderedContent,
    ResolvedRecipient,
    DeliveryStatus,
)


@pytest.fixture
def push_config():
    """Fixture de configuração de push."""
    return PushConfig(
        vapid=VAPIDConfig(
            private_key="test-private-key",
            public_key="test-public-key",
            subject="mailto:test@example.com",
        ),
        fcm=None,
        enabled=True,
    )


@pytest.fixture
def mock_db():
    """Fixture de banco de dados mock."""
    db = AsyncMock()
    return db


@pytest.fixture
def push_dispatcher(mock_db, push_config):
    """Fixture de PushDispatcher."""
    return PushDispatcher(db=mock_db, config=push_config)


@pytest.fixture
def sample_message():
    """Fixture de mensagem de teste."""
    return ChannelMessage(
        intent_id="test-intent",
        correlation_id="test-correlation",
        channel="push",
        recipient=ResolvedRecipient(
            recipient_id="user-123",
            recipient_type="user",
        ),
        content=RenderedContent(
            format="json",
            body="Teste de push notification",
            subject="Teste IntelliCare",
        ),
        metadata={"severity": "MEDIUM"},
    )


@pytest.mark.asyncio
async def test_send_to_web_subscription(push_dispatcher, mock_db, sample_message):
    """Testa envio para subscription web (VAPID)."""
    # Arrange
    subscription = PushSubscription(
        id=uuid4(),
        user_id="user-123",
        subscription_type="web",
        endpoint="https://fcm.googleapis.com/fcm/send/...",
        p256dh_key="test-p256dh",
        auth_key="test-auth",
        active=True,
    )

    # Mock do banco retornando subscription
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [subscription]
    mock_db.execute.return_value = mock_result

    # Mock do VAPID service
    with patch.object(push_dispatcher._vapid, 'send', return_value=True) as mock_send:
        # Act
        result = await push_dispatcher.send(sample_message)

        # Assert
        assert result.success is True
        assert result.metadata["sent_to"] == 1
        assert result.metadata["failed"] == 0
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_no_subscriptions(push_dispatcher, mock_db, sample_message):
    """Testa envio quando usuário não tem subscriptions."""
    # Arrange
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # Act
    result = await push_dispatcher.send(sample_message)

    # Assert
    assert result.success is False
    assert result.error_code == "no_subscriptions"


@pytest.mark.asyncio
async def test_send_to_multiple_devices(push_dispatcher, mock_db, sample_message):
    """Testa envio para múltiplos dispositivos."""
    # Arrange
    subscriptions = [
        PushSubscription(
            id=uuid4(),
            user_id="user-123",
            subscription_type="web",
            endpoint="https://fcm.googleapis.com/fcm/send/device1",
            p256dh_key="test-p256dh-1",
            auth_key="test-auth-1",
            active=True,
        ),
        PushSubscription(
            id=uuid4(),
            user_id="user-123",
            subscription_type="web",
            endpoint="https://fcm.googleapis.com/fcm/send/device2",
            p256dh_key="test-p256dh-2",
            auth_key="test-auth-2",
            active=True,
        ),
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = subscriptions
    mock_db.execute.return_value = mock_result

    # Mock do VAPID service
    with patch.object(push_dispatcher._vapid, 'send', return_value=True) as mock_send:
        # Act
        result = await push_dispatcher.send(sample_message)

        # Assert
        assert result.success is True
        assert result.metadata["sent_to"] == 2
        assert result.metadata["failed"] == 0
        assert mock_send.call_count == 2


@pytest.mark.asyncio
async def test_get_status(push_dispatcher):
    """Testa consulta de status."""
    # Act
    status = await push_dispatcher.get_status("test-message-id")

    # Assert
    assert status == DeliveryStatus.DELIVERED


@pytest.mark.asyncio
async def test_cancel(push_dispatcher):
    """Testa cancelamento (não suportado)."""
    # Act
    result = await push_dispatcher.cancel("test-message-id")

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_health_check(push_dispatcher):
    """Testa health check."""
    # Mock dos serviços
    with patch.object(push_dispatcher._vapid, 'health_check', return_value=True):
        # Act
        health = await push_dispatcher.health_check()

        # Assert
        assert health.channel == "push"
        assert health.available is True
        assert health.status == "healthy"

