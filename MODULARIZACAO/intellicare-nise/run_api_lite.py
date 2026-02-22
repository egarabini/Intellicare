
import logging
import sys
import uvicorn
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nise.lite")

# Ensure src is in path
sys.path.insert(0, ".")

# --- Mock Redis ---
# Mock redis module before importing nise
mock_redis = MagicMock()
sys.modules["redis"] = mock_redis
sys.modules["redis.asyncio"] = mock_redis

class MockKestraClient:
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
    
    async def health_check(self):
        return True

    async def list_executions(self, **kwargs):
        # Return dummy executions
        return [
            MagicMock(
                id="exec-123",
                flowId="alerta-critico-notificacao",
                namespace="intellicare",
                state="SUCCESS",
                startDate=datetime.now().isoformat(),
                endDate=datetime.now().isoformat(),
                inputs={"alerta_id": "ALT-99"},
                outputs={"notified": True},
                error=None
            ),
            MagicMock(
                id="exec-124", 
                flowId="analise-lab-florence",
                namespace="intellicare",
                state="RUNNING",
                startDate=datetime.now().isoformat(),
                endDate=None,
                inputs={"lab_id": "LAB-55"},
                outputs=None,
                error=None
            )
        ]

    async def execute_flow(self, **kwargs):
        return MagicMock(
            id=str(uuid.uuid4()),
            flowId=kwargs.get("flow_id"),
            namespace=kwargs.get("namespace"),
            state="CREATED",
            startDate=datetime.now().isoformat()
        )
    
    # trigger_workflow calls execute_flow in the real client, so we can likely remove this or alias it if needed.
    # But workflows.py now calls execute_flow directly.
    # Keeping it just in case, but updating signautre.
    async def trigger_workflow(self, request):
         return MagicMock(
            id=str(uuid.uuid4()),
            flowId=request.workflow_id,
            namespace=request.namespace,
            state="CREATED",
             startDate=datetime.now().isoformat()
        )

    async def close(self):
        pass

class MockFlowiseClient:
    def __init__(self, base_url=None, api_key=None, timeout=30.0):
        pass

    async def health_check(self):
        return True

    async def chat(self, question, **kwargs):
        # Simple rule-based mock response
        q = question.lower()
        text = "Desculpe, não entendi. Sou uma versão Lite do Dr. Nise."
        
        if "diabetes" in q:
            text = "O paciente João Silva possui Diabetes Tipo 2 diagnosticada em 2023. Última Hemoglobina Glicada: 7.2%."
        elif "alerta" in q:
            text = "Existem 2 alertas ativos: 1 Crítico (Glicemia > 300) e 1 Atenção (Pressão Arterial 140/90)."
        elif "resumo" in q:
            text = "Paciente masculino, 45 anos. Hipertenso e Diabético. Em uso de Metformina e Losartana. Adesão ao tratamento: 85%."
            
        return MagicMock(
            text=text,
            session_id=kwargs.get("session_id", "sess-mock"),
            chatflow_id=kwargs.get("chatflow_id", "mock-flow"),
            metadata={}
        )

    async def get_chatflows(self):
        return [{"id": "flow-1", "name": "Dr. Nise Main"}, {"id": "flow-2", "name": "Triagem"}]

    async def close(self):
        pass

# --- Patching & Startup ---

if __name__ == "__main__":
    try:
        from nise.api.app import app
        from nise.api.endpoints.workflows import get_kestra_client
        from nise.api.endpoints.chatbot import get_flowise_client
        
        # Override dependencies
        app.dependency_overrides[get_kestra_client] = lambda: MockKestraClient()
        app.dependency_overrides[get_flowise_client] = lambda: MockFlowiseClient()
        
        logger.info("🚀 Starting Nise API (Lite Mode) on port 8000...")
        logger.info("Simulating Kestra and Flowise services.")
        
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
    except Exception as e:
        logger.error(f"Failed to start Nise Lite: {e}")
        sys.exit(1)
