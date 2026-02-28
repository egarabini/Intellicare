"""Cliente API para comunicação com Florence backend."""

import requests
from typing import Any, Dict, List, Optional
from florence.ui.config import API_BASE_URL


class FlorenceAPIClient:
    """Cliente para interagir com a API Florence."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        """Inicializa o cliente API.
        
        Args:
            base_url: URL base da API Florence
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição GET.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros query string
            
        Returns:
            Resposta JSON
            
        Raises:
            requests.HTTPError: Se a requisição falhar
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Faz requisição POST.
        
        Args:
            endpoint: Endpoint da API
            data: Dados do body
            
        Returns:
            Resposta JSON
            
        Raises:
            requests.HTTPError: Se a requisição falhar
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    # Health & Info
    
    def get_health(self) -> Dict[str, Any]:
        """Verifica saúde da API.
        
        Returns:
            Status de saúde
        """
        return self._get("/health")
    
    def get_info(self) -> Dict[str, Any]:
        """Obtém informações do módulo.
        
        Returns:
            Informações do módulo
        """
        return self._get("/info")
    
    # Core Endpoints
    
    def get_resources(self) -> Dict[str, Any]:
        """Lista recursos disponíveis.
        
        Returns:
            Recursos (painéis, exames, correlações)
        """
        return self._get("/api/v1/resources")
    
    def interpret_labs(
        self, 
        patient_id: str, 
        results: Dict[str, float]
    ) -> Dict[str, Any]:
        """Interpreta exames laboratoriais.
        
        Args:
            patient_id: ID do paciente
            results: Dicionário {exame: valor}
            
        Returns:
            Interpretações dos exames
        """
        data = {
            "patient_id": patient_id,
            "results": results
        }
        return self._post("/api/v1/interpret", data)
    
    def analyze_labs(
        self, 
        patient_id: str, 
        results: Dict[str, float]
    ) -> Dict[str, Any]:
        """Análise completa de exames.
        
        Args:
            patient_id: ID do paciente
            results: Dicionário {exame: valor}
            
        Returns:
            Análise completa (interpretações + correlações)
        """
        data = {
            "patient_id": patient_id,
            "results": results
        }
        return self._post("/api/v1/analyze", data)
    
    def analyze_trends(
        self,
        patient_id: str,
        lab_name: str,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analisa tendências temporais.
        
        Args:
            patient_id: ID do paciente
            lab_name: Nome do exame
            historical_data: Lista de {timestamp, value}
            
        Returns:
            Análise de tendências
        """
        data = {
            "patient_id": patient_id,
            "lab_name": lab_name,
            "historical_data": historical_data
        }
        return self._post("/api/v1/analyze-trends", data)
    
    # RAG Endpoints
    
    def query_rag(
        self, 
        query: str, 
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Query direta ao RAG.
        
        Args:
            query: Query de busca
            top_k: Número de protocolos a retornar
            
        Returns:
            Protocolos relevantes
        """
        data = {
            "query": query,
            "top_k": top_k
        }
        return self._post("/api/v1/rag/query", data)
    
    def get_protocols(self) -> Dict[str, Any]:
        """Lista protocolos indexados.
        
        Returns:
            Lista de protocolos
        """
        return self._get("/api/v1/rag/protocols")
    
    def analyze_with_rag(
        self,
        patient_id: str,
        results: Dict[str, float],
        rag_query: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Análise com protocolos RAG.
        
        Args:
            patient_id: ID do paciente
            results: Dicionário {exame: valor}
            rag_query: Query customizada (opcional, auto-gerada se None)
            top_k: Número de protocolos a retornar
            
        Returns:
            Análise completa + protocolos relevantes
        """
        data = {
            "patient_id": patient_id,
            "results": results,
            "top_k": top_k
        }
        if rag_query:
            data["rag_query"] = rag_query
        return self._post("/api/v1/analyze-with-rag", data)

