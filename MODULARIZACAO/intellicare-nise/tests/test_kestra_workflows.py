"""
Testes para integração com Kestra workflows.

Testa:
- Cliente Kestra
- Endpoints REST de workflows
- Disparo de workflows
- Consulta de execuções
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from nise.api.app import app
from nise.services.kestra_client import (
    KestraClient,
    WorkflowTriggerRequest,
    WorkflowExecution,
    WorkflowExecutionStatus,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def kestra_client():
    """Fixture para cliente Kestra mockado."""
    return KestraClient(base_url="http://localhost:8080", api_key="test-key")


@pytest.fixture
def test_client():
    """Fixture para cliente de teste FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_execution():
    """Fixture para execução mockada."""
    return WorkflowExecution(
        execution_id="exec-123",
        workflow_id="alerta-critico-notificacao",
        namespace="intellicare",
        status=WorkflowExecutionStatus.SUCCESS,
        start_date="2026-02-15T10:00:00Z",
        end_date="2026-02-15T10:01:30Z",
        duration=90.0,
        inputs={"paciente_id": "pac-123", "alerta_id": "alerta-456"},
        outputs={"email_sent": True, "rocketchat_sent": True},
        error=None,
    )


# ── Testes do Cliente Kestra ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trigger_workflow(kestra_client, mock_execution):
    """Testa disparo de workflow."""
    with patch.object(kestra_client, 'client') as mock_client:
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "exec-123",
            "flowId": "alerta-critico-notificacao",
            "namespace": "intellicare",
            "state": {"current": "SUCCESS"},
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        
        # Trigger workflow
        request = WorkflowTriggerRequest(
            workflow_id="alerta-critico-notificacao",
            namespace="intellicare",
            inputs={"paciente_id": "pac-123", "alerta_id": "alerta-456"},
        )
        
        execution = await kestra_client.trigger_workflow(request)
        
        # Assertions
        assert execution.execution_id == "exec-123"
        assert execution.workflow_id == "alerta-critico-notificacao"
        assert execution.namespace == "intellicare"
        assert execution.status == WorkflowExecutionStatus.SUCCESS


@pytest.mark.asyncio
async def test_get_execution(kestra_client, mock_execution):
    """Testa consulta de execução."""
    with patch.object(kestra_client, 'client') as mock_client:
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "exec-123",
            "flowId": "alerta-critico-notificacao",
            "namespace": "intellicare",
            "state": {"current": "SUCCESS", "startDate": "2026-02-15T10:00:00Z", "endDate": "2026-02-15T10:01:30Z"},
            "inputs": {"paciente_id": "pac-123", "alerta_id": "alerta-456"},
            "outputs": {"email_sent": True},
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        
        # Get execution
        execution = await kestra_client.get_execution("exec-123")
        
        # Assertions
        assert execution.execution_id == "exec-123"
        assert execution.status == WorkflowExecutionStatus.SUCCESS
        assert execution.inputs["paciente_id"] == "pac-123"


@pytest.mark.asyncio
async def test_list_executions(kestra_client):
    """Testa listagem de execuções."""
    with patch.object(kestra_client, 'client') as mock_client:
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "exec-123",
                    "flowId": "alerta-critico-notificacao",
                    "namespace": "intellicare",
                    "state": {"current": "SUCCESS"},
                },
                {
                    "id": "exec-456",
                    "flowId": "reclassificacao-plano",
                    "namespace": "intellicare",
                    "state": {"current": "RUNNING"},
                },
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        
        # List executions
        executions = await kestra_client.list_executions(limit=10)
        
        # Assertions
        assert len(executions) == 2
        assert executions[0].execution_id == "exec-123"
        assert executions[1].execution_id == "exec-456"


@pytest.mark.asyncio
async def test_health_check(kestra_client):
    """Testa health check."""
    with patch.object(kestra_client, 'client') as mock_client:
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get = AsyncMock(return_value=mock_response)
        
        # Health check
        is_healthy = await kestra_client.health_check()
        
        # Assertions
        assert is_healthy is True


# ── Testes dos Endpoints REST ──────────────────────────────────────────────

def test_trigger_workflow_endpoint(test_client):
    """Testa endpoint de disparo de workflow."""
    with patch("nise.api.endpoints.workflows.get_kestra_client") as mock_get_client:
        # Mock client
        mock_client = AsyncMock()
        mock_client.trigger_workflow = AsyncMock(return_value=WorkflowExecution(
            execution_id="exec-123",
            workflow_id="alerta-critico-notificacao",
            namespace="intellicare",
            status=WorkflowExecutionStatus.CREATED,
            start_date="2026-02-15T10:00:00Z",
            inputs={"paciente_id": "pac-123"},
        ))
        mock_get_client.return_value = mock_client
        
        # Request
        response = test_client.post(
            "/api/v1/workflows/trigger",
            json={
                "workflow_id": "alerta-critico-notificacao",
                "namespace": "intellicare",
                "inputs": {"paciente_id": "pac-123", "alerta_id": "alerta-456"},
            },
        )
        
        # Assertions
        assert response.status_code == 202
        data = response.json()
        assert data["execution_id"] == "exec-123"
        assert data["workflow_id"] == "alerta-critico-notificacao"


def test_get_execution_endpoint(test_client):
    """Testa endpoint de consulta de execução."""
    with patch("nise.api.endpoints.workflows.get_kestra_client") as mock_get_client:
        # Mock client
        mock_client = AsyncMock()
        mock_client.get_execution = AsyncMock(return_value=WorkflowExecution(
            execution_id="exec-123",
            workflow_id="alerta-critico-notificacao",
            namespace="intellicare",
            status=WorkflowExecutionStatus.SUCCESS,
            start_date="2026-02-15T10:00:00Z",
            end_date="2026-02-15T10:01:30Z",
            duration=90.0,
            inputs={"paciente_id": "pac-123"},
            outputs={"email_sent": True},
        ))
        mock_get_client.return_value = mock_client

        # Request
        response = test_client.get("/api/v1/workflows/executions/exec-123")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == "exec-123"
        assert data["status"] == "SUCCESS"
        assert data["duration"] == 90.0


def test_list_executions_endpoint(test_client):
    """Testa endpoint de listagem de execuções."""
    with patch("nise.api.endpoints.workflows.get_kestra_client") as mock_get_client:
        # Mock client
        mock_client = AsyncMock()
        mock_client.list_executions = AsyncMock(return_value=[
            WorkflowExecution(
                execution_id="exec-123",
                workflow_id="alerta-critico-notificacao",
                namespace="intellicare",
                status=WorkflowExecutionStatus.SUCCESS,
                start_date="2026-02-15T10:00:00Z",
                inputs={},
            ),
            WorkflowExecution(
                execution_id="exec-456",
                workflow_id="reclassificacao-plano",
                namespace="intellicare",
                status=WorkflowExecutionStatus.RUNNING,
                start_date="2026-02-15T10:05:00Z",
                inputs={},
            ),
        ])
        mock_get_client.return_value = mock_client

        # Request
        response = test_client.get("/api/v1/workflows/executions?limit=10")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["execution_id"] == "exec-123"
        assert data[1]["execution_id"] == "exec-456"


def test_health_check_endpoint(test_client):
    """Testa endpoint de health check."""
    with patch("nise.api.endpoints.workflows.get_kestra_client") as mock_get_client:
        # Mock client
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client

        # Request
        response = test_client.get("/api/v1/workflows/health")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Kestra está operacional" in data["message"]


def test_get_workflow_endpoint(test_client):
    """Testa endpoint de consulta de workflow."""
    with patch("nise.api.endpoints.workflows.get_kestra_client") as mock_get_client:
        # Mock client
        mock_client = AsyncMock()
        mock_client.get_workflow = AsyncMock(return_value={
            "id": "alerta-critico-notificacao",
            "namespace": "intellicare",
            "description": "Workflow para processar alertas críticos",
            "inputs": [
                {"id": "paciente_id", "type": "STRING", "required": True},
                {"id": "alerta_id", "type": "STRING", "required": True},
            ],
            "tasks": [],
        })
        mock_get_client.return_value = mock_client

        # Request
        response = test_client.get("/api/v1/workflows/workflows/alerta-critico-notificacao")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "alerta-critico-notificacao"
        assert data["namespace"] == "intellicare"
        assert len(data["inputs"]) == 2

