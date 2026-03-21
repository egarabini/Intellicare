"""Testes da Fase E do CarePlanner: Kestra Workflows e Start Journey."""
import pytest
from httpx import AsyncClient, ConnectError, Response
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from intellicare_core.contracts.base import TenantContext
from modules.careplanner.adapters.kestra import KestraAdapter
from modules.careplanner.config import CareplannerSettings
from modules.careplanner.services import CareplannerService
from modules.careplanner.api.routes import router

app = FastAPI()
app.include_router(router, prefix="/careplanner")

@pytest.fixture
def mock_settings():
    return CareplannerSettings(
        kestra_url="http://kestra-mock:8080",
        kestra_api_key="mocked-api-key",
    )


@pytest.fixture
def kestra_adapter(mock_settings):
    return KestraAdapter(mock_settings)


@pytest.mark.asyncio
async def test_trigger_flow_sucesso(kestra_adapter, respx_mock):
    # Mocka httpx.AsyncClient.post retornando {"id": "exec-123", "state": "RUNNING"}
    respx_mock.post("http://kestra-mock:8080/api/v1/executions/intellicare.careplanner/careplanner_jornada_basica").mock(
        return_value=Response(200, json={"id": "exec-123", "state": "RUNNING"})
    )

    result = await kestra_adapter.trigger_flow(
        namespace="intellicare.careplanner",
        flow_id="careplanner_jornada_basica",
        inputs={"patient_ref": "123"}
    )
    
    assert result == {"id": "exec-123", "state": "RUNNING"}


@pytest.mark.asyncio
async def test_trigger_flow_kestra_indisponivel(kestra_adapter, respx_mock):
    # Mocka httpx para lançar httpx.ConnectError
    respx_mock.post("http://kestra-mock:8080/api/v1/executions/intellicare.careplanner/careplanner_jornada_basica").mock(
        side_effect=ConnectError("Connection refused")
    )
    
    repo = MagicMock()
    rc = MagicMock()
    jitsi = MagicMock()
    whatsapp_mock = MagicMock()
    whatsapp_mock.send_message = AsyncMock(return_value={"key": {"id": "mock-wa"}})
    whatsapp_mock.close = AsyncMock()
    email_mock = MagicMock()
    email_mock.send_message = AsyncMock(return_value={"data": {}})
    email_mock.close = AsyncMock()
    sms_mock = MagicMock()
    sms_mock.send_message = AsyncMock(return_value={"status": "sent"})
    sms_mock.close = AsyncMock()
    service = CareplannerService(
        repo=repo,
        rc=rc,
        jitsi=jitsi,
        kestra=kestra_adapter,
        whatsapp=whatsapp_mock,
        email=email_mock,
        sms=sms_mock,
    )
    
    ctx = TenantContext.from_slug("alfa", "user123")
    
    class MockBody:
        patient_ref = "123"
        task_type = "CHECK_IN"
        template_code = "foo"
        template_variables = {}
        contact_phone_e164 = "+55"
        contact_email = None
        flow_id = "careplanner_jornada_basica"
        clinico_ref = None
        appointment_id = None

    with pytest.raises(HTTPException) as excinfo:
        await service.trigger_journey(ctx, MockBody())
    
    assert excinfo.value.status_code == 502
    assert excinfo.value.detail["error"] == "kestra_unavailable"


@pytest.mark.asyncio
async def test_trigger_journey_endpoint_202():
    # Usa TestClient com dependencias mockadas
    mock_service = AsyncMock()
    mock_service.trigger_journey.return_value = {"ok": True, "execution_id": "exec-123", "status": "CREATED"}
    
    async def override_get_service():
        return mock_service

    async def override_get_current_tenant():
        return TenantContext.from_slug("alfa", "user123", roles=["GESTOR"])

    from modules.careplanner.api.routes import get_service
    from intellicare_core.auth.jwt import get_current_tenant
    
    app.dependency_overrides[get_service] = override_get_service
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant

    client = TestClient(app)
    
    response = client.post(
        "/careplanner/journeys/trigger",
        json={
            "patient_ref": "paciente-123",
            "task_type": "CHECK_IN",
            "flow_id": "careplanner_jornada_basica"
        },
        headers={"Authorization": "Bearer mocked_token"}
    )
    
    assert response.status_code == 202
    assert response.json() == {"ok": True, "execution_id": "exec-123", "status": "CREATED"}
    mock_service.trigger_journey.assert_called_once()


def test_seed_flows_idempotente(respx_mock):
    # Mocka httpx.post retornando Response(200, ...)
    respx_mock.post("http://localhost:8080/api/v1/flows").mock(return_value=Response(200, json={}))
    
    import infra.kestra.seed_flows as seed_module
    
    # Chama provision_flows() duas vezes
    seed_module.provision_flows()
    seed_module.provision_flows()
    
    # Sao 9 flows por execucao; duas execucoes devem resultar em 18 chamadas.
    assert respx_mock.calls.call_count == 18
