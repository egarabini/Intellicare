"""Cliente HTTP para Kestra API."""

import httpx
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Models ──────────────────────────────────────────────────────────────────────────────────────


class ExecutionRequest(BaseModel):
    """Request para executar workflow."""
    inputs: Optional[Dict[str, Any]] = None
    labels: Optional[Dict[str, str]] = None
    wait: bool = False


class ExecutionResponse(BaseModel):
    """Response de execução de workflow."""
    id: str
    namespace: str
    flowId: str
    state: str
    startDate: str
    endDate: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None


class FlowResponse(BaseModel):
    """Response de workflow."""
    id: str
    namespace: str
    revision: int
    description: Optional[str] = None
    labels: Optional[Dict[str, str]] = None


# ── Kestra Client ───────────────────────────────────────────────────────────────────────────────


class KestraClient:
    """
    Cliente HTTP para Kestra API.
    
    Permite executar workflows, consultar execuções e gerenciar flows.
    
    **Exemplo de uso**:
    ```python
    client = KestraClient(base_url="http://localhost:8080")
    
    # Executar workflow
    execution = await client.execute_flow(
        namespace="intellicare",
        flow_id="alerta-critico-notificacao",
        inputs={"paciente_id": "pac-123", "alerta_id": "alerta-456"}
    )
    
    # Consultar execução
    status = await client.get_execution(execution.id)
    ```
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Inicializa cliente Kestra.
        
        Args:
            base_url: URL base do Kestra (default: http://localhost:8080)
            api_key: API key para autenticação (opcional)
            timeout: Timeout em segundos (default: 30.0)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers
        )
    
    async def execute_flow(
        self,
        namespace: str,
        flow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
        wait: bool = False
    ) -> ExecutionResponse:
        """
        Executa um workflow.
        
        Args:
            namespace: Namespace do workflow (ex: 'intellicare')
            flow_id: ID do workflow (ex: 'alerta-critico-notificacao')
            inputs: Inputs para o workflow
            labels: Labels para a execução
            wait: Se True, aguarda conclusão do workflow
        
        Returns:
            ExecutionResponse com dados da execução
        
        Raises:
            httpx.HTTPStatusError: Se a requisição falhar
        """
        url = f"{self.base_url}/api/v1/executions/{namespace}/{flow_id}"
        
        payload = ExecutionRequest(
            inputs=inputs or {},
            labels=labels or {},
            wait=wait
        )
        
        logger.info(f"Executing flow: {namespace}/{flow_id}")
        logger.debug(f"Inputs: {inputs}")
        
        response = await self.client.post(
            url,
            json=payload.model_dump(exclude_none=True)
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Execution started: {data['id']}")
        
        return ExecutionResponse(**data)
    
    async def get_execution(self, execution_id: str) -> ExecutionResponse:
        """
        Consulta status de uma execução.
        
        Args:
            execution_id: ID da execução
        
        Returns:
            ExecutionResponse com dados atualizados
        """
        url = f"{self.base_url}/api/v1/executions/{execution_id}"
        
        response = await self.client.get(url)
        response.raise_for_status()
        
        return ExecutionResponse(**response.json())
    
    async def list_executions(
        self,
        namespace: Optional[str] = None,
        flow_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 10
    ) -> List[ExecutionResponse]:
        """
        Lista execuções.
        
        Args:
            namespace: Filtrar por namespace
            flow_id: Filtrar por flow_id
            state: Filtrar por estado (SUCCESS, FAILED, RUNNING, etc.)
            limit: Número máximo de resultados
        
        Returns:
            Lista de ExecutionResponse
        """
        url = f"{self.base_url}/api/v1/executions"
        
        params = {"size": limit}
        if namespace:
            params["namespace"] = namespace
        if flow_id:
            params["flowId"] = flow_id
        if state:
            params["state"] = state
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return [ExecutionResponse(**item) for item in data.get("results", [])]
    
    async def get_flow(self, namespace: str, flow_id: str) -> FlowResponse:
        """
        Busca detalhes de um workflow.
        
        Args:
            namespace: Namespace do workflow
            flow_id: ID do workflow
        
        Returns:
            FlowResponse com dados do workflow
        """
        url = f"{self.base_url}/api/v1/flows/{namespace}/{flow_id}"
        
        response = await self.client.get(url)
        response.raise_for_status()
        
        return FlowResponse(**response.json())
    
    async def health_check(self) -> bool:
        """
        Verifica se Kestra está disponível.
        
        Returns:
            True se Kestra está saudável, False caso contrário
        """
        try:
            url = f"{self.base_url}/health"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self):
        """Fecha conexão HTTP."""
        await self.client.aclose()

