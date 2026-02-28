"""
Testes para SMSDispatcher (D4).

Testa envio de SMS via múltiplos providers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from comunicacao.channels.sms.config import SMSConfig, TwilioConfig
from comunicacao.channels.sms.dispatcher import SMSDispatcher
from comunicacao.dispatchers.base import (
    ChannelMessage,
    RenderedContent,
    ResolvedRecipient,
    DeliveryStatus,
)


@pytest.fixture
def sms_config():
    """Fixture de configuração de SMS."""
    return SMSConfig(
        twilio=TwilioConfig(
            account_sid="test-sid",
            auth_token="test-token",
            from_number="+15551234567",
            enabled=True,
        ),
        default_provider="twilio",
        enabled=True,
    )


@pytest.fixture
def mock_db():
    """Fixture de banco de dados mock."""
    db = AsyncMock()
    return db


@pytest.fixture
def sms_dispatcher(mock_db, sms_config):
    """Fixture de SMSDispatcher."""
    return SMSDispatcher(db=mock_db, config=sms_config)


@pytest.fixture
def sample_message():
    """Fixture de mensagem de teste."""
    return ChannelMessage(
        intent_id="test-intent",
        correlation_id="test-correlation",
        channel="sms",
        recipient=ResolvedRecipient(
            recipient_id="+5511999999999",
            recipient_type="phone",
        ),
        content=RenderedContent(
            format="text",
            body="Lembrete: consulta amanhã às 14h",
            subject="",
        ),
        metadata={},
    )


@pytest.mark.asyncio
async def test_send_sms_twilio(sms_dispatcher, mock_db, sample_message):
    """Testa envio de SMS via Twilio."""
    # Arrange
    mock_response = {
        "message_id": "SM123456",
        "status": "sent",
        "to": "+5511999999999",
    }

    # Mock do provider
    with patch.object(
        sms_dispatcher._providers["twilio"], "send", return_value=mock_response
    ) as mock_send:
        # Act
        result = await sms_dispatcher.send(sample_message)

        # Assert
        assert result.success is True
        assert result.channel_message_id == "SM123456"
        assert result.metadata["provider"] == "twilio"
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_no_provider(mock_db):
    """Testa envio sem provider configurado."""
    # Arrange
    config = SMSConfig(enabled=True, default_provider="twilio")
    dispatcher = SMSDispatcher(db=mock_db, config=config)

    message = ChannelMessage(
        intent_id="test-intent",
        correlation_id="test-correlation",
        channel="sms",
        recipient=ResolvedRecipient(
            recipient_id="+5511999999999",
            recipient_type="phone",
        ),
        content=RenderedContent(format="text", body="Teste", subject=""),
        metadata={},
    )

    # Act
    result = await dispatcher.send(message)

    # Assert
    assert result.success is False
    assert result.error_code == "no_provider"


@pytest.mark.asyncio
async def test_get_status(sms_dispatcher, mock_db):
    """Testa consulta de status."""
    # Arrange
    from comunicacao.channels.models import ExternalMessageLog, ExternalMessageStatus

    log = ExternalMessageLog(
        channel="sms",
        direction="outbound",
        provider_message_id="SM123456",
        status=ExternalMessageStatus.DELIVERED,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = log
    mock_db.execute.return_value = mock_result

    # Act
    status = await sms_dispatcher.get_status("SM123456")

    # Assert
    assert status == DeliveryStatus.DELIVERED


@pytest.mark.asyncio
async def test_cancel(sms_dispatcher):
    """Testa cancelamento (não suportado)."""
    # Act
    result = await sms_dispatcher.cancel("SM123456")

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_health_check(sms_dispatcher):
    """Testa health check."""
    # Mock do provider
    with patch.object(sms_dispatcher._providers["twilio"], "health_check", return_value=True):
        # Act
        health = await sms_dispatcher.health_check()

        # Assert
        assert health.channel == "sms"
        assert health.available is True
        assert health.status == "healthy"


@pytest.mark.asyncio
async def test_validate_recipient_valid(sms_dispatcher):
    """Testa validação de destinatário válido."""
    # Arrange
    recipient = ResolvedRecipient(
        recipient_id="+5511999999999",
        recipient_type="phone",
    )

    # Act
    validation = await sms_dispatcher.validate_recipient(recipient)

    # Assert
    assert validation.valid is True


@pytest.mark.asyncio
async def test_validate_recipient_invalid(sms_dispatcher):
    """Testa validação de destinatário inválido."""
    # Arrange
    recipient = ResolvedRecipient(
        recipient_id="11999999999",  # Sem +
        recipient_type="phone",
    )

    # Act
    validation = await sms_dispatcher.validate_recipient(recipient)

    # Assert
    assert validation.valid is False
    assert "+" in validation.error_message

