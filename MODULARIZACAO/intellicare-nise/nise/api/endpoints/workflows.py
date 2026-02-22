"""
Endpoints REST para gerenciamento de workflows Kestra.

Este módulo fornece endpoints para:
- Disparar workflows manualmente
- Consultar execuções de workflows
- Verificar status de workflows
- Health check do Kestra
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from nise.services.kestra_client import (
    KestraClient,
    ExecutionRequest,
    ExecutionResponse,
)


# ── Schemas ─────────────────────────────────────────────────────────────────

class TriggerWorkflowRequest(BaseModel):
    """Request para disparar workflow."""
    
    workflow_id: str = Field(..., description="ID do workflow (ex: alerta-critico-notificacao)")
    namespace: str = Field(default="intellicare", description="Namespace do workflow")
    inputs: Dict[str, str] = Field(default_factory=dict, description="Inputs do workflow")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "alerta-critico-notificacao",
                "namespace": "intellicare",
                "inputs": {
                    "paciente_id": "pac-123",
                    "alerta_id": "alerta-456",
                    "tipo_alerta": "critico",
                    "mensagem": "Glicemia crítica: 350 mg/dL"
                }
            }
        }


class TriggerWorkflowResponse(BaseModel):
    """Response do disparo de workflow."""
    
    execution_id: str = Field(..., description="ID da execução")
    workflow_id: str = Field(..., description="ID do workflow")
    namespace: str = Field(..., description="Namespace")
    status: str = Field(..., description="Status inicial")
    message: str = Field(..., description="Mensagem de confirmação")


class WorkflowExecutionResponse(BaseModel):
    """Response com detalhes da execução."""
    
    execution_id: str
    workflow_id: str
    namespace: str
    status: str
    start_date: str
    end_date: Optional[str] = None
    duration: Optional[float] = None
    inputs: Dict[str, str]
    outputs: Optional[Dict] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response do health check."""
    
    status: str = Field(..., description="Status do Kestra (healthy/unhealthy)")
    version: Optional[str] = Field(None, description="Versão do Kestra")
    message: str = Field(..., description="Mensagem de status")


# ── Router ──────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ── Dependency Injection ────────────────────────────────────────────────────

def get_kestra_client() -> KestraClient:
    """Dependency para obter cliente Kestra."""
    from nise.config import settings
    return KestraClient(base_url=settings.kestra_url, api_key=settings.kestra_api_key)


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/trigger", response_model=TriggerWorkflowResponse, status_code=202)
async def trigger_workflow(
    request: TriggerWorkflowRequest,
    kestra: KestraClient = Depends(get_kestra_client),
):
    """
    Dispara um workflow manualmente.
    
    **Workflows disponíveis**:
    - `alerta-critico-notificacao`: Processa alertas críticos
    - `reclassificacao-plano`: Reclassifica planos de cuidado
    - `acompanhamento-periodico`: Acompanhamento periódico de pacientes
    
    **Exemplo**:
    ```json
    {
        "workflow_id": "alerta-critico-notificacao",
        "namespace": "intellicare",
        "inputs": {
            "paciente_id": "pac-123",
            "alerta_id": "alerta-456",
            "tipo_alerta": "critico",
            "mensagem": "Glicemia crítica: 350 mg/dL"
        }
    }
    ```
    """
    try:
        trigger_req = ExecutionRequest(
            inputs=request.inputs,
            # namespace e workflow_id são passados no método execute_flow, não no request body
        )
        
        execution = await kestra.execute_flow(
            namespace=request.namespace,
            flow_id=request.workflow_id,
            inputs=request.inputs
        )
        
        return TriggerWorkflowResponse(
            execution_id=execution.id,
            workflow_id=execution.flowId,
            namespace=execution.namespace,
            status=execution.state,
            message=f"Workflow '{request.workflow_id}' disparado com sucesso",
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao disparar workflow: {str(e)}")


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: str,
    kestra: KestraClient = Depends(get_kestra_client),
):
    """
    Consulta detalhes de uma execução de workflow.
    
    **Retorna**:
    - Status da execução (CREATED, RUNNING, SUCCESS, FAILED)
    - Inputs fornecidos
    - Outputs gerados (se concluído)
    - Erro (se falhou)
    - Duração (se concluído)
    """
    try:
        execution = await kestra.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail=f"Execução '{execution_id}' não encontrada")
        
        return WorkflowExecutionResponse(
            execution_id=execution.id,
            workflow_id=execution.flowId,
            namespace=execution.namespace,
            status=execution.state,
            start_date=execution.startDate,
            end_date=execution.endDate,
            duration=None, # Mock/API não retorna duração direta
            inputs=execution.inputs or {},
            outputs=execution.outputs,
            error=None,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar execução: {str(e)}")


@router.get("/executions", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: Optional[str] = Query(None, description="Filtrar por workflow ID"),
    namespace: str = Query("intellicare", description="Namespace"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(10, ge=1, le=100, description="Limite de resultados"),
    kestra: KestraClient = Depends(get_kestra_client),
):
    """
    Lista execuções de workflows.

    **Filtros disponíveis**:
    - `workflow_id`: Filtrar por workflow específico
    - `status`: Filtrar por status (CREATED, RUNNING, SUCCESS, FAILED)
    - `limit`: Número máximo de resultados (1-100)

    **Exemplo**:
    ```
    GET /api/v1/workflows/executions?workflow_id=alerta-critico-notificacao&status=SUCCESS&limit=20
    ```
    """
    try:
        executions = await kestra.list_executions(
            workflow_id=workflow_id,
            namespace=namespace,
            status=status,
            limit=limit,
        )

        return [
            WorkflowExecutionResponse(
                execution_id=exec.id,
                workflow_id=exec.flowId,
                namespace=exec.namespace,
                status=exec.state,
                start_date=exec.startDate,
                end_date=exec.endDate,
                duration=None,
                inputs=exec.inputs or {},
                outputs=exec.outputs,
                error=None,
            )
            for exec in executions
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar execuções: {str(e)}")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    kestra: KestraClient = Depends(get_kestra_client),
):
    """
    Verifica status do Kestra.

    **Retorna**:
    - `status`: healthy ou unhealthy
    - `version`: Versão do Kestra
    - `message`: Mensagem de status
    """
    try:
        is_healthy = await kestra.health_check()

        if is_healthy:
            return HealthCheckResponse(
                status="healthy",
                version="0.15.0",  # TODO: Obter versão real da API
                message="Kestra está operacional",
            )
        else:
            return HealthCheckResponse(
                status="unhealthy",
                message="Kestra não está respondendo",
            )

    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            message=f"Erro ao verificar Kestra: {str(e)}",
        )


@router.get("/workflows/{workflow_id}", response_model=Dict)
async def get_workflow(
    workflow_id: str,
    namespace: str = Query("intellicare", description="Namespace"),
    kestra: KestraClient = Depends(get_kestra_client),
):
    """
    Consulta definição de um workflow.

    **Retorna**:
    - Definição completa do workflow (YAML convertido para JSON)
    - Inputs esperados
    - Triggers configurados
    - Tasks definidas
    """
    try:
        workflow = await kestra.get_workflow(workflow_id, namespace)

        if not workflow:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_id}' não encontrado no namespace '{namespace}'",
            )

        return workflow

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar workflow: {str(e)}")

