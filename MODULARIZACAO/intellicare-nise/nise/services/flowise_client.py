"""Cliente para integração com Flowise."""

import httpx
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ── Models ─────────────────────────────────────────────────────────────────


class ChatMessage(BaseModel):
    """Mensagem de chat."""
    
    role: str  # 'user', 'assistant', 'system'
    content: str


class ChatRequest(BaseModel):
    """Request para chat."""
    
    question: str
    chatflow_id: str = "dr-nise-default"
    session_id: Optional[str] = None
    streaming: bool = False


class ChatResponse(BaseModel):
    """Response do chat."""
    
    text: str
    session_id: str
    chatflow_id: str
    metadata: Optional[Dict[str, Any]] = None


# ── Client ─────────────────────────────────────────────────────────────────


class FlowiseClient:
    """Cliente para API Flowise."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Inicializa cliente Flowise.
        
        Args:
            base_url: URL base do Flowise
            api_key: API key (opcional)
            timeout: Timeout em segundos
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
        
        logger.info(f"FlowiseClient initialized: {base_url}")
    
    async def chat(
        self,
        question: str,
        chatflow_id: str = "dr-nise-default",
        session_id: Optional[str] = None,
        streaming: bool = False
    ) -> ChatResponse:
        """
        Envia mensagem para chatbot.
        
        Args:
            question: Pergunta do usuário
            chatflow_id: ID do chatflow
            session_id: ID da sessão (opcional)
            streaming: Habilitar streaming
            
        Returns:
            ChatResponse com resposta do chatbot
        """
        try:
            url = f"{self.base_url}/api/v1/prediction/{chatflow_id}"
            
            payload = {
                "question": question,
                "streaming": streaming
            }
            
            if session_id:
                payload["sessionId"] = session_id
            
            logger.info(f"Sending chat request: {question[:50]}...")
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return ChatResponse(
                text=data.get("text", ""),
                session_id=data.get("sessionId", session_id or ""),
                chatflow_id=chatflow_id,
                metadata=data.get("metadata")
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def get_chatflows(self) -> List[Dict[str, Any]]:
        """
        Lista todos os chatflows disponíveis.
        
        Returns:
            Lista de chatflows
        """
        try:
            url = f"{self.base_url}/api/v1/chatflows"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def get_chatflow(self, chatflow_id: str) -> Dict[str, Any]:
        """
        Busca detalhes de um chatflow específico.
        
        Args:
            chatflow_id: ID do chatflow
            
        Returns:
            Detalhes do chatflow
        """
        try:
            url = f"{self.base_url}/api/v1/chatflows/{chatflow_id}"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Verifica se Flowise está disponível.
        
        Returns:
            True se disponível, False caso contrário
        """
        try:
            url = f"{self.base_url}/api/v1/health"
            
            response = await self.client.get(url)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self):
        """Fecha conexão HTTP."""
        await self.client.aclose()
        logger.info("FlowiseClient closed")

