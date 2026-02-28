"""
Testes para SMS Providers (D4).

Testa providers Twilio, Zenvia e SNS.
"""

import pytest
from unittest.mock import AsyncMock, patch

from comunicacao.channels.sms.config import TwilioConfig, ZenviaConfig, SNSConfig
from comunicacao.channels.sms.providers import (
    TwilioSMSProvider,
    ZenviaSMSProvider,
    SNSSMSProvider,
)


@pytest.fixture
def twilio_config():
    """Fixture de configuração Twilio."""
    return TwilioConfig(
        account_sid="test-sid",
        auth_token="test-token",
        from_number="+15551234567",
        enabled=True,
    )


@pytest.fixture
def zenvia_config():
    """Fixture de configuração Zenvia."""
    return ZenviaConfig(
        api_token="test-token",
        from_name="IntelliCare",
        enabled=True,
    )


@pytest.fixture
def sns_config():
    """Fixture de configuração SNS."""
    return SNSConfig(
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        aws_region="us-east-1",
        enabled=True,
    )


@pytest.mark.asyncio
async def test_twilio_send(twilio_config):
    """Testa envio via Twilio."""
    # Arrange
    provider = TwilioSMSProvider(twilio_config)
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "sid": "SM123456",
        "status": "sent",
        "to": "+5511999999999",
    }
    mock_response.raise_for_status = AsyncMock()

    # Mock do client
    with patch.object(provider._client, "post", return_value=mock_response):
        # Act
        result = await provider.send(to="+5511999999999", text="Teste")

        # Assert
        assert result["message_id"] == "SM123456"
        assert result["status"] == "sent"


@pytest.mark.asyncio
async def test_twilio_validate_phone(twilio_config):
    """Testa validação de número Twilio."""
    # Arrange
    provider = TwilioSMSProvider(twilio_config)

    # Act & Assert
    assert provider.validate_phone_number("+5511999999999") is True
    assert provider.validate_phone_number("11999999999") is False
    assert provider.validate_phone_number("+55119") is False


@pytest.mark.asyncio
async def test_twilio_truncate_message(twilio_config):
    """Testa truncamento de mensagem."""
    # Arrange
    provider = TwilioSMSProvider(twilio_config)
    long_text = "A" * 200

    # Act
    truncated = provider.truncate_message(long_text, max_length=160)

    # Assert
    assert len(truncated) == 160
    assert truncated.endswith("...")


@pytest.mark.asyncio
async def test_zenvia_send(zenvia_config):
    """Testa envio via Zenvia."""
    # Arrange
    provider = ZenviaSMSProvider(zenvia_config)
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "id": "ZV123456",
    }
    mock_response.raise_for_status = AsyncMock()

    # Mock do client
    with patch.object(provider._client, "post", return_value=mock_response):
        # Act
        result = await provider.send(to="+5511999999999", text="Teste")

        # Assert
        assert result["message_id"] == "ZV123456"
        assert result["status"] == "sent"


@pytest.mark.asyncio
async def test_zenvia_get_status(zenvia_config):
    """Testa consulta de status Zenvia (não suportado)."""
    # Arrange
    provider = ZenviaSMSProvider(zenvia_config)

    # Act
    status = await provider.get_status("ZV123456")

    # Assert
    assert status is None


@pytest.mark.asyncio
async def test_sns_send_not_implemented(sns_config):
    """Testa envio via SNS (não implementado)."""
    # Arrange
    provider = SNSSMSProvider(sns_config)

    # Act & Assert
    with pytest.raises(NotImplementedError):
        await provider.send(to="+5511999999999", text="Teste")


@pytest.mark.asyncio
async def test_sns_health_check(sns_config):
    """Testa health check SNS."""
    # Arrange
    provider = SNSSMSProvider(sns_config)

    # Act
    is_healthy = await provider.health_check()

    # Assert
    assert is_healthy is True  # Credenciais configuradas


@pytest.mark.asyncio
async def test_sns_health_check_no_credentials():
    """Testa health check SNS sem credenciais."""
    # Arrange
    config = SNSConfig(
        aws_access_key_id="",
        aws_secret_access_key="",
        aws_region="us-east-1",
        enabled=True,
    )
    provider = SNSSMSProvider(config)

    # Act
    is_healthy = await provider.health_check()

    # Assert
    assert is_healthy is False

