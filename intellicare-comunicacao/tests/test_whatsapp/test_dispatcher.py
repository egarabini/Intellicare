"""
Testes para WhatsAppDispatcher (D4).

Testa envio de mensagens WhatsApp via Meta Graph API.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from comunicacao.channels.whatsapp.config import WhatsAppConfig
from comunicacao.channels.whatsapp.dispatcher import WhatsAppDispatcher
from comunicacao.dispatchers.base import (
    ChannelMessage,
    RenderedContent,
    ResolvedRecipient,
    DeliveryStatus,
)


@pytest.fixture
def whatsapp_config():
    """Fixture de configuração de WhatsApp."""
    return WhatsAppConfig(
        phone_number_id="123456789",
        business_account_id="987654321",
        access_token="test-token",
        webhook_verify_token="test-verify-token",
        enabled=True,
    )


@pytest.fixture
def mock_db():
    """Fixture de banco de dados mock."""
    db = AsyncMock()
    return db


@pytest.fixture
def whatsapp_dispatcher(mock_db, whatsapp_config):
    """Fixture de WhatsAppDispatcher."""
    return WhatsAppDispatcher(db=mock_db, config=whatsapp_config)


@pytest.fixture
def sample_message():
    """Fixture de mensagem de teste."""
    return ChannelMessage(
        intent_id="test-intent",
        correlation_id="test-correlation",
        channel="whatsapp",
        recipient=ResolvedRecipient(
            recipient_id="+5511999999999",
            recipient_type="phone",
        ),
        content=RenderedContent(
            format="template",
            body="",
            subject="",
        ),
        metadata={
            "template_name": "alerta_clinico",
            "template_params": ["Dr. João", "Maria Santos", "eGFR < 30", "CRÍTICA"],
        },
    )


@pytest.mark.asyncio
async def test_send_template_message(whatsapp_dispatcher, mock_db, sample_message):
    """Testa envio de mensagem com template."""
    # Arrange
    mock_response = {
        "messages": [{"id": "wamid.test123"}],
        "messaging_product": "whatsapp",
    }

    # Mock do client
    with patch.object(
        whatsapp_dispatcher._client, "send_template_message", return_value=mock_response
    ) as mock_send:
        # Act
        result = await whatsapp_dispatcher.send(sample_message)

        # Assert
        assert result.success is True
        assert result.channel_message_id == "wamid.test123"
        assert result.metadata["template_name"] == "alerta_clinico"
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_missing_template(whatsapp_dispatcher, mock_db):
    """Testa envio sem template (erro)."""
    # Arrange
    message = ChannelMessage(
        intent_id="test-intent",
        correlation_id="test-correlation",
        channel="whatsapp",
        recipient=ResolvedRecipient(
            recipient_id="+5511999999999",
            recipient_type="phone",
        ),
        content=RenderedContent(format="text", body="Teste", subject=""),
        metadata={},  # Sem template_name
    )

    # Act
    result = await whatsapp_dispatcher.send(message)

    # Assert
    assert result.success is False
    assert result.error_code == "missing_template"


@pytest.mark.asyncio
async def test_get_status(whatsapp_dispatcher, mock_db):
    """Testa consulta de status."""
    # Arrange
    from comunicacao.channels.models import ExternalMessageLog, ExternalMessageStatus

    log = ExternalMessageLog(
        channel="whatsapp",
        direction="outbound",
        provider_message_id="wamid.test123",
        status=ExternalMessageStatus.DELIVERED,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = log
    mock_db.execute.return_value = mock_result

    # Act
    status = await whatsapp_dispatcher.get_status("wamid.test123")

    # Assert
    assert status == DeliveryStatus.DELIVERED


@pytest.mark.asyncio
async def test_cancel(whatsapp_dispatcher):
    """Testa cancelamento (não suportado)."""
    # Act
    result = await whatsapp_dispatcher.cancel("wamid.test123")

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_health_check(whatsapp_dispatcher):
    """Testa health check."""
    # Mock do client
    with patch.object(whatsapp_dispatcher._client, "health_check", return_value=True):
        # Act
        health = await whatsapp_dispatcher.health_check()

        # Assert
        assert health.channel == "whatsapp"
        assert health.available is True
        assert health.status == "healthy"


@pytest.mark.asyncio
async def test_validate_recipient_valid(whatsapp_dispatcher):
    """Testa validação de destinatário válido."""
    # Arrange
    recipient = ResolvedRecipient(
        recipient_id="+5511999999999",
        recipient_type="phone",
    )

    # Act
    validation = await whatsapp_dispatcher.validate_recipient(recipient)

    # Assert
    assert validation.valid is True


@pytest.mark.asyncio
async def test_validate_recipient_invalid(whatsapp_dispatcher):
    """Testa validação de destinatário inválido."""
    # Arrange
    recipient = ResolvedRecipient(
        recipient_id="11999999999",  # Sem +
        recipient_type="phone",
    )

    # Act
    validation = await whatsapp_dispatcher.validate_recipient(recipient)

    # Assert
    assert validation.valid is False
    assert "+" in validation.reason

