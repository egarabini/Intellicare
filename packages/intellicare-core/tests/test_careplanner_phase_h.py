"""Testes DEM-047 — canal WhatsApp."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from modules.careplanner.adapters.whatsapp import WhatsAppAdapter
from modules.careplanner.contracts import Channel
from modules.careplanner.config import CareplannerSettings


def make_settings(**kwargs):
    base = dict(
        evolution_api_url="http://localhost:8080",
        evolution_api_key="test-key",
        evolution_instance_name="test",
        evolution_webhook_secret="secret123",
        evolution_max_retries=3
    )
    base.update(kwargs)
    return MagicMock(**base)


@pytest.mark.asyncio
async def test_whatsapp_send_message():
    """WhatsAppAdapter.send_message chama endpoint correto."""
    settings = make_settings()
    adapter = WhatsAppAdapter(settings)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"key": {"id": "abc"}})
        mock_post.return_value.raise_for_status = lambda: None
        await adapter.send_message("+5511999999999", "Olá!")
        called_path = mock_post.call_args[0][0]
        assert "sendText/test" in called_path


def test_extract_phone_from_jid():
    """Extrai número de JID corretamente."""
    adapter = WhatsAppAdapter(make_settings())
    assert adapter.extract_phone_from_jid("5511999999999@s.whatsapp.net") == "5511999999999"


def test_verify_webhook_secret_correto():
    adapter = WhatsAppAdapter(make_settings(evolution_webhook_secret="abc123"))
    assert adapter.verify_webhook_secret("abc123") is True


def test_verify_webhook_secret_errado():
    adapter = WhatsAppAdapter(make_settings(evolution_webhook_secret="abc123"))
    assert adapter.verify_webhook_secret("errado") is False


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Sim, confirmado", "SIM"),
        ("ok", "SIM"),
        ("1", "SIM"),
        ("não vou conseguir", "NAO"),
        ("nao", "NAO"),
        ("2", "NAO"),
        ("talvez amanhã", "OUTRO"),
    ],
)
def test_normalize_confirmation_variants(text, expected):
    adapter = WhatsAppAdapter(make_settings())
    assert adapter.normalize_confirmation(text) == expected
