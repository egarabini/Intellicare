"""Phase I testes para Adapter Listmonk (DEM-048)."""
import pytest
from httpx import Response
from modules.careplanner.adapters.email import EmailAdapter
from modules.careplanner.config import CareplannerSettings


@pytest.fixture
def email_settings():
    return CareplannerSettings(
        listmonk_url="http://listmonk.test:9000",
        listmonk_username="admin",
        listmonk_password="password",
        listmonk_sender_email="test@intellicare.ia.br"
    )


@pytest.fixture
def email_adapter(email_settings):
    return EmailAdapter(email_settings)


@pytest.mark.asyncio
async def test_email_send_message_success(email_adapter, respx_mock):
    respx_mock.post("http://listmonk.test:9000/api/tx").mock(
        return_value=Response(200, json={"data": {"id": "123"}})
    )

    result = await email_adapter.send_message(
        email="paciente@test.com",
        subject="Assunto Teste",
        text="Corpo do email teste"
    )

    assert result["ok"] is True
    assert result["tx_id"] == "123"


@pytest.mark.asyncio
async def test_email_send_message_failure(email_adapter, respx_mock):
    respx_mock.post("http://listmonk.test:9000/api/tx").mock(
        return_value=Response(400, json={"message": "Invalid email"})
    )

    result = await email_adapter.send_message(
        email="invalid",
        subject="Assunto Teste",
        text="Corpo do email teste"
    )

    assert result["ok"] is False
    assert "HTTP 400" in result["error"]


@pytest.mark.asyncio
async def test_email_send_message_retry_5xx(email_adapter, respx_mock):
    # Simula falha 502 seguida de sucesso 200
    route = respx_mock.post("http://listmonk.test:9000/api/tx")
    route.side_effect = [
        Response(502, text="Bad Gateway"),
        Response(200, json={"data": {"id": "124"}}),
    ]

    result = await email_adapter.send_message(
        email="retry@test.com",
        subject="Retry Test",
        text="Retry Body"
    )

    assert result["ok"] is True
    assert result["tx_id"] == "124"
    assert route.call_count == 2
