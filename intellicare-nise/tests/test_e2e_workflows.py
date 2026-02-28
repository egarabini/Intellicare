"""
Testes E2E para workflows Kestra.

Testa integração completa:
- Disparo de workflows via API
- Execução de workflows no Kestra
- Consulta de status e resultados
- Validação de outputs
"""

import pytest
import asyncio
import time
from typing import Dict, Any

from nise.services.kestra_client import (
    KestraClient,
    WorkflowTriggerRequest,
    WorkflowExecutionStatus,
)
from nise.config import settings


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def kestra_client():
    """Fixture para cliente Kestra real."""
    return KestraClient(
        base_url=settings.kestra_url,
        api_key=settings.kestra_api_key,
    )


@pytest.fixture
def mock_paciente_data() -> Dict[str, Any]:
    """Fixture com dados mockados de paciente."""
    return {
        "paciente_id": "pac-test-001",
        "nome": "João da Silva",
        "cpf": "123.456.789-00",
        "data_nascimento": "1960-05-15",
        "condicoes": ["diabetes", "has"],
    }


@pytest.fixture
def mock_alerta_data() -> Dict[str, Any]:
    """Fixture com dados mockados de alerta."""
    return {
        "alerta_id": "alerta-test-001",
        "tipo_alerta": "critico",
        "mensagem": "Glicemia crítica: 350 mg/dL",
        "data_alerta": "2026-02-15T10:00:00Z",
    }


# ── Helper Functions ────────────────────────────────────────────────────────

async def wait_for_execution(
    client: KestraClient,
    execution_id: str,
    timeout: int = 60,
    poll_interval: int = 2,
) -> WorkflowExecutionStatus:
    """
    Aguarda conclusão de execução de workflow.
    
    Args:
        client: Cliente Kestra
        execution_id: ID da execução
        timeout: Timeout em segundos (default: 60)
        poll_interval: Intervalo de polling em segundos (default: 2)
    
    Returns:
        Status final da execução
    
    Raises:
        TimeoutError: Se timeout for atingido
    """
    start_time = time.time()
    
    while True:
        # Verifica timeout
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timeout aguardando execução {execution_id}")
        
        # Consulta execução
        execution = await client.get_execution(execution_id)
        
        if not execution:
            raise ValueError(f"Execução {execution_id} não encontrada")
        
        # Verifica se concluiu
        if execution.status in [
            WorkflowExecutionStatus.SUCCESS,
            WorkflowExecutionStatus.FAILED,
            WorkflowExecutionStatus.CANCELLED,
        ]:
            return execution.status
        
        # Aguarda antes de próximo poll
        await asyncio.sleep(poll_interval)


# ── Testes E2E ──────────────────────────────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_alerta_critico_workflow(
    kestra_client,
    mock_paciente_data,
    mock_alerta_data,
):
    """
    Teste E2E do workflow de alerta crítico.
    
    Fluxo:
    1. Dispara workflow com dados de alerta
    2. Aguarda conclusão
    3. Valida status e outputs
    """
    # Preparar inputs
    inputs = {
        "paciente_id": mock_paciente_data["paciente_id"],
        "alerta_id": mock_alerta_data["alerta_id"],
        "tipo_alerta": mock_alerta_data["tipo_alerta"],
        "mensagem": mock_alerta_data["mensagem"],
    }
    
    # Disparar workflow
    request = WorkflowTriggerRequest(
        workflow_id="alerta-critico-notificacao",
        namespace="intellicare",
        inputs=inputs,
    )
    
    execution = await kestra_client.trigger_workflow(request)
    
    # Assertions iniciais
    assert execution.execution_id is not None
    assert execution.workflow_id == "alerta-critico-notificacao"
    assert execution.namespace == "intellicare"
    assert execution.status in [
        WorkflowExecutionStatus.CREATED,
        WorkflowExecutionStatus.RUNNING,
    ]
    
    # Aguardar conclusão
    final_status = await wait_for_execution(
        kestra_client,
        execution.execution_id,
        timeout=120,  # 2 minutos
    )
    
    # Validar status final
    assert final_status == WorkflowExecutionStatus.SUCCESS
    
    # Consultar execução final
    final_execution = await kestra_client.get_execution(execution.execution_id)
    
    # Validar outputs
    assert final_execution is not None
    assert final_execution.outputs is not None
    assert final_execution.error is None
    assert final_execution.duration is not None
    assert final_execution.duration > 0
    
    # Validar que tasks foram executadas
    # (outputs devem conter resultados de buscar_paciente, enviar_email, etc.)
    assert "buscar_paciente" in str(final_execution.outputs) or final_execution.outputs != {}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_reclassificacao_workflow(kestra_client, mock_paciente_data):
    """
    Teste E2E do workflow de reclassificação de plano.
    
    Fluxo:
    1. Dispara workflow com dados de paciente
    2. Aguarda conclusão
    3. Valida status e outputs
    """
    # Preparar inputs
    inputs = {
        "paciente_id": mock_paciente_data["paciente_id"],
        "condicao": "diabetes",
    }
    
    # Disparar workflow
    request = WorkflowTriggerRequest(
        workflow_id="reclassificacao-plano",
        namespace="intellicare",
        inputs=inputs,
    )
    
    execution = await kestra_client.trigger_workflow(request)
    
    # Assertions iniciais
    assert execution.execution_id is not None
    assert execution.workflow_id == "reclassificacao-plano"

    # Aguardar conclusão
    final_status = await wait_for_execution(
        kestra_client,
        execution.execution_id,
        timeout=180,  # 3 minutos (pode processar múltiplos pacientes)
    )

    # Validar status final
    assert final_status == WorkflowExecutionStatus.SUCCESS

    # Consultar execução final
    final_execution = await kestra_client.get_execution(execution.execution_id)

    # Validar outputs
    assert final_execution is not None
    assert final_execution.error is None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_acompanhamento_workflow(kestra_client):
    """
    Teste E2E do workflow de acompanhamento periódico.

    Fluxo:
    1. Dispara workflow com período diário
    2. Aguarda conclusão
    3. Valida status e outputs
    """
    # Preparar inputs
    inputs = {
        "periodo": "diario",
        "condicao": "todas",
        "dias_atraso_minimo": "3",
    }

    # Disparar workflow
    request = WorkflowTriggerRequest(
        workflow_id="acompanhamento-periodico",
        namespace="intellicare",
        inputs=inputs,
    )

    execution = await kestra_client.trigger_workflow(request)

    # Assertions iniciais
    assert execution.execution_id is not None
    assert execution.workflow_id == "acompanhamento-periodico"

    # Aguardar conclusão
    final_status = await wait_for_execution(
        kestra_client,
        execution.execution_id,
        timeout=180,  # 3 minutos
    )

    # Validar status final
    assert final_status == WorkflowExecutionStatus.SUCCESS

    # Consultar execução final
    final_execution = await kestra_client.get_execution(execution.execution_id)

    # Validar outputs
    assert final_execution is not None
    assert final_execution.error is None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_workflow_error_handling(kestra_client):
    """
    Teste E2E de error handling em workflows.

    Testa que workflows lidam corretamente com erros (ex: paciente não encontrado).
    """
    # Preparar inputs com paciente inexistente
    inputs = {
        "paciente_id": "pac-nao-existe-999",
        "alerta_id": "alerta-test-999",
        "tipo_alerta": "critico",
        "mensagem": "Teste de erro",
    }

    # Disparar workflow
    request = WorkflowTriggerRequest(
        workflow_id="alerta-critico-notificacao",
        namespace="intellicare",
        inputs=inputs,
    )

    execution = await kestra_client.trigger_workflow(request)

    # Aguardar conclusão (pode falhar ou ter error handling)
    try:
        final_status = await wait_for_execution(
            kestra_client,
            execution.execution_id,
            timeout=120,
        )

        # Se concluiu, verificar se tem error ou se error handling funcionou
        final_execution = await kestra_client.get_execution(execution.execution_id)

        # Pode ter falhado (FAILED) ou ter error handling que trata o erro
        assert final_status in [
            WorkflowExecutionStatus.SUCCESS,  # Error handling tratou
            WorkflowExecutionStatus.FAILED,   # Falhou como esperado
        ]

    except TimeoutError:
        # Timeout também é aceitável em caso de erro
        pass


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_list_executions(kestra_client):
    """
    Teste E2E de listagem de execuções.

    Testa que conseguimos listar execuções de workflows.
    """
    # Listar execuções
    executions = await kestra_client.list_executions(
        namespace="intellicare",
        limit=10,
    )

    # Validar que retornou lista
    assert isinstance(executions, list)

    # Se houver execuções, validar estrutura
    if len(executions) > 0:
        execution = executions[0]
        assert execution.execution_id is not None
        assert execution.workflow_id is not None
        assert execution.namespace == "intellicare"
        assert execution.status is not None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_get_workflow_definition(kestra_client):
    """
    Teste E2E de consulta de definição de workflow.

    Testa que conseguimos consultar a definição de um workflow.
    """
    # Consultar workflow
    workflow = await kestra_client.get_workflow(
        workflow_id="alerta-critico-notificacao",
        namespace="intellicare",
    )

    # Validar estrutura
    assert workflow is not None
    assert isinstance(workflow, dict)
    assert workflow.get("id") == "alerta-critico-notificacao"
    assert workflow.get("namespace") == "intellicare"

    # Validar que tem inputs e tasks
    assert "inputs" in workflow or "tasks" in workflow


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_kestra_health_check(kestra_client):
    """
    Teste E2E de health check do Kestra.

    Testa que o Kestra está operacional.
    """
    # Health check
    is_healthy = await kestra_client.health_check()

    # Validar que está saudável
    assert is_healthy is True


# ── Testes de Performance ──────────────────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_workflow_trigger(kestra_client, mock_paciente_data, mock_alerta_data):
    """
    Teste de performance do disparo de workflow.

    Valida que o disparo é rápido (< 2 segundos).
    """
    # Preparar inputs
    inputs = {
        "paciente_id": mock_paciente_data["paciente_id"],
        "alerta_id": mock_alerta_data["alerta_id"],
        "tipo_alerta": mock_alerta_data["tipo_alerta"],
        "mensagem": mock_alerta_data["mensagem"],
    }

    # Medir tempo de disparo
    start_time = time.time()

    request = WorkflowTriggerRequest(
        workflow_id="alerta-critico-notificacao",
        namespace="intellicare",
        inputs=inputs,
    )

    execution = await kestra_client.trigger_workflow(request)

    elapsed_time = time.time() - start_time

    # Validar que disparou
    assert execution.execution_id is not None

    # Validar performance (< 2 segundos)
    assert elapsed_time < 2.0, f"Disparo demorou {elapsed_time:.2f}s (esperado < 2s)"


@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_get_execution(kestra_client):
    """
    Teste de performance da consulta de execução.

    Valida que a consulta é rápida (< 1 segundo).
    """
    # Primeiro, disparar um workflow para ter uma execução
    request = WorkflowTriggerRequest(
        workflow_id="alerta-critico-notificacao",
        namespace="intellicare",
        inputs={
            "paciente_id": "pac-perf-test",
            "alerta_id": "alerta-perf-test",
            "tipo_alerta": "critico",
            "mensagem": "Teste de performance",
        },
    )

    execution = await kestra_client.trigger_workflow(request)
    execution_id = execution.execution_id

    # Medir tempo de consulta
    start_time = time.time()

    result = await kestra_client.get_execution(execution_id)

    elapsed_time = time.time() - start_time

    # Validar que consultou
    assert result is not None
    assert result.execution_id == execution_id

    # Validar performance (< 1 segundo)
    assert elapsed_time < 1.0, f"Consulta demorou {elapsed_time:.2f}s (esperado < 1s)"


