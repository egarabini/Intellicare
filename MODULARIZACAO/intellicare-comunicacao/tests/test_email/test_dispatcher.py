"""
Testes para EmailDispatcher (D4.5).

Testa envio de Email via SMTP provider.
"""

import pytest
from unittest.mock import AsyncMock, patch

from comunicacao.channels.email.config import EmailConfig, SMTPConfig
from comunicacao.channels.email.dispatcher import EmailDispatcher
from comunicacao.dispatchers.base import (
    ChannelMessage,
    RenderedContent,
    ResolvedRecipient,
)


@pytest.fixture
def email_config():
    return EmailConfig(
        smtp=SMTPConfig(
            host="localhost",
            port=1025,
            sender_email="test@example.com",
            use_tls=False,
        ),
    )


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def email_dispatcher(mock_db, email_config):
    return EmailDispatcher(db=mock_db, config=email_config)


@pytest.fixture
def sample_message():
    return ChannelMessage(
        intent_id="test-intent",
        correlation_id="test-correlation",
        channel="email",
        recipient=ResolvedRecipient(
            recipient_id="user@example.com",
            recipient_type="email",
        ),
        content=RenderedContent(
            format="text",
            body="Hello World",
            subject="Test Subject",
        ),
        metadata={},
    )


@pytest.mark.asyncio
async def test_send_email_success(email_dispatcher, mock_db, sample_message):
    """Testa envio de email com sucesso."""
    with patch.object(email_dispatcher.provider, "send", return_value=True):
        result = await email_dispatcher.send(sample_message)

        assert result.success is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_failure(email_dispatcher, mock_db, sample_message):
    """Testa falha no envio de email."""
    with patch.object(email_dispatcher.provider, "send", return_value=False):
        result = await email_dispatcher.send(sample_message)

        assert result.success is False
        assert result.error_code == "send_failed"


@pytest.mark.asyncio
async def test_validate_recipient_valid(email_dispatcher):
    """Testa validação de destinatário válido."""
    recipient = ResolvedRecipient(recipient_id="valid@email.com", recipient_type="email")
    result = await email_dispatcher.validate_recipient(recipient)
    assert result.valid is True
    assert result.recipient_id == "valid@email.com"


@pytest.mark.asyncio
async def test_validate_recipient_invalid(email_dispatcher):
    """Testa validação de destinatário inválido."""
    recipient = ResolvedRecipient(recipient_id="invalid-email", recipient_type="email")
    result = await email_dispatcher.validate_recipient(recipient)
    assert result.valid is False
    assert result.error_code == "invalid_format"


@pytest.mark.asyncio
async def test_health_check(email_dispatcher):
    """Testa health check."""
    with patch.object(email_dispatcher.provider, "health_check", return_value={"status": "healthy"}):
        health = await email_dispatcher.health_check()
        assert health.status == "healthy"
        assert health.available is True
