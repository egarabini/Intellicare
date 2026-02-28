"""
Testes para WhatsAppWebhookHandler (D4).

Testa processamento de webhooks da Meta.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

from comunicacao.channels.whatsapp.webhook_handler import WhatsAppWebhookHandler


@pytest.fixture
def mock_db():
    """Fixture de banco de dados mock."""
    db = AsyncMock()
    return db


@pytest.fixture
def webhook_handler(mock_db):
    """Fixture de WhatsAppWebhookHandler."""
    return WhatsAppWebhookHandler(db=mock_db)


@pytest.fixture
def status_update_payload():
    """Fixture de payload de status update."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "5511999999999",
                                "phone_number_id": "123456789",
                            },
                            "statuses": [
                                {
                                    "id": "wamid.test123",
                                    "status": "delivered",
                                    "timestamp": "1708444800",
                                    "recipient_id": "5511888888888",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def incoming_message_payload():
    """Fixture de payload de mensagem recebida."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "5511999999999",
                                "phone_number_id": "123456789",
                            },
                            "messages": [
                                {
                                    "from": "5511888888888",
                                    "id": "wamid.incoming123",
                                    "timestamp": "1708444800",
                                    "type": "text",
                                    "text": {"body": "Tomei a medicação"},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_handle_status_update(webhook_handler, mock_db, status_update_payload):
    """Testa processamento de status update."""
    # Act
    await webhook_handler.handle_webhook(status_update_payload)

    # Assert
    # Verificar que execute foi chamado (update no banco)
    assert mock_db.execute.called
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_handle_incoming_message(webhook_handler, mock_db, incoming_message_payload):
    """Testa processamento de mensagem recebida."""
    # Act
    await webhook_handler.handle_webhook(incoming_message_payload)

    # Assert
    # Verificar que add foi chamado (criar log)
    assert mock_db.add.called
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_handle_invalid_webhook(webhook_handler, mock_db):
    """Testa webhook inválido."""
    # Arrange
    invalid_payload = {"object": "invalid"}

    # Act
    await webhook_handler.handle_webhook(invalid_payload)

    # Assert
    # Não deve processar nada
    assert not mock_db.execute.called
    assert not mock_db.add.called


def test_verify_webhook_valid(webhook_handler):
    """Testa verificação de webhook válida."""
    # Act
    result = webhook_handler.verify_webhook(
        mode="subscribe",
        token="test-token",
        challenge="test-challenge",
        verify_token="test-token",
    )

    # Assert
    assert result == "test-challenge"


def test_verify_webhook_invalid_token(webhook_handler):
    """Testa verificação de webhook com token inválido."""
    # Act
    result = webhook_handler.verify_webhook(
        mode="subscribe",
        token="wrong-token",
        challenge="test-challenge",
        verify_token="test-token",
    )

    # Assert
    assert result is None


def test_verify_webhook_invalid_mode(webhook_handler):
    """Testa verificação de webhook com mode inválido."""
    # Act
    result = webhook_handler.verify_webhook(
        mode="invalid",
        token="test-token",
        challenge="test-challenge",
        verify_token="test-token",
    )

    # Assert
    assert result is None

