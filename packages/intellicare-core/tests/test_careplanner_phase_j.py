"""Testes DEM-049 — canal SMS via Jasmin."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from modules.careplanner.adapters.sms import SMSAdapter
from modules.careplanner.contracts import Channel


def make_settings(**kwargs):
    base = dict(
        jasmin_url="http://localhost:1401",
        jasmin_username="admin",
        jasmin_password="test",
        jasmin_sender_id="TEST",
        jasmin_webhook_secret="secret",
    )
    base.update(kwargs)
    return MagicMock(**base)


@pytest.mark.asyncio
async def test_sms_send_message():
    adapter = SMSAdapter(make_settings())
    mock_response = MagicMock(status_code=200, text='Success "abc123"')
    mock_response.raise_for_status = lambda: None
    with patch.object(adapter, "_get_client") as mock_client:
        client = AsyncMock()
        client.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = client
        result = await adapter.send_message("+5511999999999", "Teste SMS")
        assert result["status"] == "sent"
        assert "abc123" in result["jasmin_response"]


def test_channel_sms_exists():
    assert Channel.SMS == "sms"


def test_sms_normalize_phone():
    adapter = SMSAdapter(make_settings())
    assert adapter._normalize_phone("+5511999") == "5511999"
    assert adapter._normalize_phone("5511999") == "5511999"


def test_sms_verify_secret():
    adapter = SMSAdapter(make_settings(jasmin_webhook_secret="abc"))
    assert adapter.verify_webhook_secret("abc") is True
    assert adapter.verify_webhook_secret("errado") is False
