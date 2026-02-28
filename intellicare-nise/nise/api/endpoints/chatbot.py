"""Endpoints para chatbot NISE."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from nise.services.flowise_client import FlowiseClient, ChatRequest, ChatResponse
from nise.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


# ── Dependencies ───────────────────────────────────────────────────────────


def get_flowise_client() -> FlowiseClient:
    """Dependency para FlowiseClient."""
    return FlowiseClient(
        base_url=settings.flowise_url,
        api_key=settings.flowise_api_key,
        timeout=30.0
    )


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    flowise: FlowiseClient = Depends(get_flowise_client)
):
    """
    Envia mensagem para o chatbot Dr. Nise.
    
    **Exemplo de uso**:
    ```json
    {
        "question": "Qual o diagnóstico de diabetes do paciente pac-123?",
        "chatflow_id": "dr-nise-default",
        "session_id": "session-abc-123"
    }
    ```
    
    **Perguntas suportadas**:
    - "Qual o diagnóstico de diabetes do paciente {id}?"
    - "Quais alertas ativos para o paciente {id}?"
    - "Qual o plano de cuidado do paciente {id}?"
    - "Me dê um resumo do paciente {id}"
    """
    try:
        logger.info(f"Chat request: {request.question[:50]}...")
        
        response = await flowise.chat(
            question=request.question,
            chatflow_id=request.chatflow_id,
            session_id=request.session_id,
            streaming=request.streaming
        )
        
        await flowise.close()
        
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatflows")
async def list_chatflows(
    flowise: FlowiseClient = Depends(get_flowise_client)
):
    """
    Lista todos os chatflows disponíveis.
    
    **Retorna**:
    - Lista de chatflows configurados no Flowise
    """
    try:
        chatflows = await flowise.get_chatflows()
        await flowise.close()
        
        return {
            "total": len(chatflows),
            "chatflows": chatflows
        }
        
    except Exception as e:
        logger.error(f"Error listing chatflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatflows/{chatflow_id}")
async def get_chatflow(
    chatflow_id: str,
    flowise: FlowiseClient = Depends(get_flowise_client)
):
    """
    Busca detalhes de um chatflow específico.
    
    **Parâmetros**:
    - `chatflow_id`: ID do chatflow (ex: 'dr-nise-default')
    """
    try:
        chatflow = await flowise.get_chatflow(chatflow_id)
        await flowise.close()
        
        return chatflow
        
    except Exception as e:
        logger.error(f"Error getting chatflow: {e}")
        raise HTTPException(status_code=404, detail=f"Chatflow not found: {chatflow_id}")


@router.get("/health")
async def chatbot_health(
    flowise: FlowiseClient = Depends(get_flowise_client)
):
    """
    Verifica se o chatbot está disponível.
    
    **Retorna**:
    - `status`: 'healthy' ou 'unhealthy'
    - `flowise_available`: True/False
    """
    try:
        is_healthy = await flowise.health_check()
        await flowise.close()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "flowise_available": is_healthy,
            "flowise_url": settings.flowise_url
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "flowise_available": False,
            "error": str(e)
        }


@router.post("/test")
async def test_chatbot(
    paciente_id: str = Query(..., description="ID do paciente para teste"),
    flowise: FlowiseClient = Depends(get_flowise_client)
):
    """
    Testa o chatbot com perguntas pré-definidas.
    
    **Parâmetros**:
    - `paciente_id`: ID do paciente (ex: 'pac-123')
    
    **Testa 3 perguntas**:
    1. Diagnósticos
    2. Alertas
    3. Resumo
    """
    try:
        perguntas = [
            f"Qual o diagnóstico de diabetes do paciente {paciente_id}?",
            f"Quais alertas ativos para o paciente {paciente_id}?",
            f"Me dê um resumo do paciente {paciente_id}"
        ]
        
        resultados = []
        
        for pergunta in perguntas:
            response = await flowise.chat(
                question=pergunta,
                chatflow_id="dr-nise-default"
            )
            
            resultados.append({
                "pergunta": pergunta,
                "resposta": response.text,
                "session_id": response.session_id
            })
        
        await flowise.close()
        
        return {
            "paciente_id": paciente_id,
            "total_perguntas": len(perguntas),
            "resultados": resultados
        }
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

