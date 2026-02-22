"""Tests for DrNiseGateway pipeline (EF-W013)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from wanda.nise.gateway import DrNiseGateway
from wanda.nise.models import PatientMessage, DrNiseResponse, NiseSession, FlowiseResponse


@pytest.fixture
def mock_flowise():
    client = MagicMock()
    client.predict = AsyncMock(return_value=FlowiseResponse(
        text="Beba água e descanse.", success=True
    ))
    client.health_check = AsyncMock(return_value=True)
    return client


@pytest.fixture
def gateway(mock_flowise):
    return DrNiseGateway(
        flowise_client=mock_flowise,
        escalation_enabled=True,
    )


class TestDrNiseGateway:
    @pytest.mark.asyncio
    async def test_chat_returns_response(self, gateway):
        msg = PatientMessage(patient_id="p1", content="Tenho dor de cabeça")
        response = await gateway.chat(msg)
        assert isinstance(response, DrNiseResponse)
        assert response.session_id is not None
        assert response.text == "Beba água e descanse."
        assert not response.flagged

    @pytest.mark.asyncio
    async def test_new_session_created(self, gateway):
        msg = PatientMessage(patient_id="p1", content="Olá")
        response = await gateway.chat(msg)
        assert response.session_id is not None
        assert response.message_count >= 1

    @pytest.mark.asyncio
    async def test_existing_session_reused(self, gateway):
        msg1 = PatientMessage(patient_id="p1", content="Mensagem 1")
        r1 = await gateway.chat(msg1)
        session_id = r1.session_id

        msg2 = PatientMessage(patient_id="p1", content="Mensagem 2", session_id=session_id)
        r2 = await gateway.chat(msg2)
        assert r2.session_id == session_id
        assert r2.message_count >= 2

    @pytest.mark.asyncio
    async def test_flowise_failure_returns_fallback(self, gateway, mock_flowise):
        mock_flowise.predict.return_value = FlowiseResponse(
            text="", success=False, error="timeout"
        )
        msg = PatientMessage(patient_id="p1", content="Teste")
        response = await gateway.chat(msg)
        assert response.text  # fallback message returned
        assert not response.flagged

    @pytest.mark.asyncio
    async def test_dangerous_response_flagged(self, gateway, mock_flowise):
        # Use exact pattern that matches: "pare" + short distance + "remedio"
        mock_flowise.predict.return_value = FlowiseResponse(
            text="Pare o remedio imediatamente.", success=True
        )
        msg = PatientMessage(patient_id="p1", content="Posso parar insulina?")
        response = await gateway.chat(msg)
        assert response.flagged
        assert response.text != "Pare o remedio imediatamente."

    @pytest.mark.asyncio
    async def test_escalation_triggers_alert_hub(self, mock_flowise):
        alert_hub = MagicMock()
        alert_hub.receive_alert = AsyncMock(return_value=MagicMock(status="accepted"))
        mock_flowise.predict.return_value = FlowiseResponse(
            text="Quero morrer.", success=True
        )
        gw = DrNiseGateway(
            flowise_client=mock_flowise,
            alert_hub=alert_hub,
            escalation_enabled=True,
        )
        msg = PatientMessage(patient_id="p1", content="estou mal")
        response = await gw.chat(msg)
        # Escalation should be triggered
        assert response.escalated
        alert_hub.receive_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_escalation_when_disabled(self, mock_flowise):
        alert_hub = MagicMock()
        alert_hub.receive_alert = AsyncMock()
        mock_flowise.predict.return_value = FlowiseResponse(
            text="Quero morrer.", success=True
        )
        gw = DrNiseGateway(
            flowise_client=mock_flowise,
            alert_hub=alert_hub,
            escalation_enabled=False,
        )
        msg = PatientMessage(patient_id="p1", content="estou mal")
        response = await gw.chat(msg)
        alert_hub.receive_alert.assert_not_called()

    @pytest.mark.asyncio
    async def test_flowise_health_check(self, gateway, mock_flowise):
        assert await gateway.flowise_health() is True

    @pytest.mark.asyncio
    async def test_end_session(self, gateway):
        msg = PatientMessage(patient_id="p1", content="Olá")
        response = await gateway.chat(msg)
        result = await gateway.end_session(response.session_id, "p1")
        assert result is True

    @pytest.mark.asyncio
    async def test_ips_loader_called(self, mock_flowise):
        ips_loader = AsyncMock(return_value={"conditions": [{"code": "E11", "display": "DM2"}]})
        gw = DrNiseGateway(flowise_client=mock_flowise, ips_loader=ips_loader)
        msg = PatientMessage(patient_id="p1", content="Tenho diabetes")
        await gw.chat(msg)
        ips_loader.assert_called_once_with("p1")
