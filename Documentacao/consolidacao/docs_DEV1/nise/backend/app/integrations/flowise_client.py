"""
============================================================================
NISE TRAINING MODULE - FLOWISE CLIENT
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Cliente para integração com Flowise API
Versão: 1.0
Data: 11/03/2026
Responsável: DEV2
============================================================================
"""

import httpx
from typing import Dict, List, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# FLOWISE CLIENT
# ============================================================================

class FlowiseClient:
    """Cliente para integração com Flowise API"""
    
    def __init__(
        self, 
        base_url: str = None,
        api_key: str = None
    ):
        """
        Inicializar cliente Flowise.
        
        Args:
            base_url: URL base do Flowise (padrão: settings.FLOWISE_URL)
            api_key: API key do Flowise (opcional)
        """
        self.base_url = base_url or settings.FLOWISE_URL
        self.api_key = api_key or settings.FLOWISE_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Fechar cliente HTTP"""
        await self.client.aclose()
    
    # ========================================================================
    # CHATFLOW METHODS
    # ========================================================================
    
    async def predict(
        self,
        chatflow_id: str,
        question: str,
        session_id: Optional[str] = None,
        overrideConfig: Optional[Dict] = None
    ) -> Dict:
        """
        Enviar mensagem para chatflow e obter resposta.
        
        Args:
            chatflow_id: ID do chatflow
            question: Pergunta do usuário
            session_id: ID da sessão (para manter contexto)
            overrideConfig: Configurações customizadas
        
        Returns:
            dict: Resposta do chatflow
        """
        url = f"{self.base_url}/api/v1/prediction/{chatflow_id}"
        
        payload = {
            "question": question
        }
        
        if session_id:
            payload["sessionId"] = session_id
        
        if overrideConfig:
            payload["overrideConfig"] = overrideConfig
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.post(
                url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Flowise API error: {e}")
            raise
    
    async def get_chatflows(self) -> List[Dict]:
        """
        Listar todos os chatflows disponíveis.
        
        Returns:
            list: Lista de chatflows
        """
        url = f"{self.base_url}/api/v1/chatflows"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Flowise API error: {e}")
            raise
    
    async def get_chatflow(self, chatflow_id: str) -> Dict:
        """
        Obter detalhes de um chatflow específico.
        
        Args:
            chatflow_id: ID do chatflow
        
        Returns:
            dict: Detalhes do chatflow
        """
        url = f"{self.base_url}/api/v1/chatflows/{chatflow_id}"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Flowise API error: {e}")
            raise
    
    # ========================================================================
    # NISE SPECIFIC METHODS
    # ========================================================================
    
    async def ask_dr_nise(
        self,
        question: str,
        session_id: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Enviar pergunta para o chatbot "Dr. Nise".
        
        Args:
            question: Pergunta do usuário
            session_id: ID da sessão de treinamento
            context: Contexto adicional (paciente, cenário, etc)
        
        Returns:
            dict: Resposta do Dr. Nise
        """
        # ID do chatflow "Dr. Nise" (será configurado no Flowise)
        dr_nise_chatflow_id = settings.FLOWISE_DR_NISE_CHATFLOW_ID
        
        # Adicionar contexto à pergunta se fornecido
        if context:
            question_with_context = f"""
Contexto:
- Paciente: {context.get('patient_name', 'N/A')}
- Cenário: {context.get('scenario_title', 'N/A')}
- Módulo: {context.get('module', 'N/A')}

Pergunta: {question}
"""
        else:
            question_with_context = question
        
        return await self.predict(
            chatflow_id=dr_nise_chatflow_id,
            question=question_with_context,
            session_id=session_id
        )
    
    async def evaluate_clinical_decision(
        self,
        scenario_id: str,
        user_decision: str,
        patient_data: Dict
    ) -> Dict:
        """
        Avaliar decisão clínica usando LLM.
        
        Args:
            scenario_id: ID do cenário clínico
            user_decision: Decisão tomada pelo usuário
            patient_data: Dados do paciente
        
        Returns:
            dict: Avaliação da decisão
        """
        # ID do chatflow de avaliação (será configurado no Flowise)
        evaluation_chatflow_id = settings.FLOWISE_EVALUATION_CHATFLOW_ID
        
        evaluation_prompt = f"""
Avalie a seguinte decisão clínica:

Cenário: {scenario_id}
Paciente: {patient_data.get('name', 'N/A')}
Dados clínicos: {patient_data.get('clinical_summary', 'N/A')}

Decisão do usuário: {user_decision}

Por favor, avalie:
1. A decisão está correta? (Sim/Não)
2. Justificativa
3. Sugestões de melhoria
4. Score (0-100)
"""
        
        return await self.predict(
            chatflow_id=evaluation_chatflow_id,
            question=evaluation_prompt
        )

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_flowise_client: Optional[FlowiseClient] = None

def get_flowise_client() -> FlowiseClient:
    """Obter instância singleton do cliente Flowise"""
    global _flowise_client
    if _flowise_client is None:
        _flowise_client = FlowiseClient()
    return _flowise_client

