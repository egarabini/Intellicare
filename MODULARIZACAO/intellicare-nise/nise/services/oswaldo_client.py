"""Cliente HTTP para integração com Oswaldo API."""

import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ── Modelos de Resposta ──────────────────────────────────────────


class DiagnosticoResponse(BaseModel):
    """Resposta de diagnóstico do Oswaldo."""
    
    paciente_id: str
    condicao: str  # "diabetes", "has", "drc"
    classificacao: str  # "tipo_2", "estagio_1", etc.
    estadiamento: str  # "A1", "Estagio 1", etc.
    data_diagnostico: str
    plano_cuidado_id: Optional[str] = None
    observacoes: Optional[str] = None


class AlertaResponse(BaseModel):
    """Resposta de alerta do Oswaldo."""
    
    alerta_id: str
    tipo: str  # "critico", "medio", "baixo"
    mensagem: str
    data_criacao: str
    status: str  # "ativo", "resolvido"
    paciente_id: str
    condicao_relacionada: Optional[str] = None


class PlanoCuidadoResponse(BaseModel):
    """Resposta de plano de cuidado do Oswaldo."""
    
    plano_id: str
    paciente_id: str
    condicao: str
    objetivos: List[str]
    intervencoes: List[Dict[str, Any]]
    metas: List[Dict[str, Any]]
    data_criacao: str
    data_atualizacao: Optional[str] = None
    status: str  # "ativo", "concluido", "cancelado"


class ResumoPacienteResponse(BaseModel):
    """Resumo completo do paciente."""
    
    paciente_id: str
    diagnosticos: List[DiagnosticoResponse]
    alertas_criticos: List[str]
    total_alertas: int
    plano_cuidado_atual: Optional[PlanoCuidadoResponse] = None
    risco_framingham: Optional[float] = None  # Futuro


# ── Cliente Oswaldo ───────────────────────────────────────────────


class OswaldoClient:
    """Cliente HTTP para API Oswaldo."""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8002",
        timeout: float = 10.0
    ):
        """
        Inicializa cliente Oswaldo.
        
        Args:
            base_url: URL base da API Oswaldo
            timeout: Timeout em segundos
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"OswaldoClient initialized: base_url={base_url}")
    
    async def close(self):
        """Fecha conexão HTTP."""
        await self.client.aclose()
    
    async def get_diagnosticos(
        self, 
        paciente_id: str
    ) -> List[DiagnosticoResponse]:
        """
        Busca diagnósticos do paciente.
        
        Args:
            paciente_id: ID do paciente
            
        Returns:
            Lista de diagnósticos
            
        Raises:
            httpx.HTTPStatusError: Se API retornar erro
        """
        try:
            logger.debug(f"Fetching diagnosticos for paciente_id={paciente_id}")
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/diagnostico/{paciente_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            diagnosticos = [DiagnosticoResponse(**d) for d in data]
            
            logger.info(f"Found {len(diagnosticos)} diagnosticos for paciente_id={paciente_id}")
            return diagnosticos
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching diagnosticos: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching diagnosticos: {e}")
            raise
    
    async def get_alertas(
        self, 
        paciente_id: str,
        status: str = "ativo"
    ) -> List[AlertaResponse]:
        """
        Busca alertas do paciente.
        
        Args:
            paciente_id: ID do paciente
            status: Status dos alertas ("ativo", "resolvido", "todos")
            
        Returns:
            Lista de alertas
        """
        try:
            logger.debug(f"Fetching alertas for paciente_id={paciente_id}, status={status}")
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/alertas/{paciente_id}",
                params={"status": status}
            )
            response.raise_for_status()
            
            data = response.json()
            alertas = [AlertaResponse(**a) for a in data]
            
            logger.info(f"Found {len(alertas)} alertas for paciente_id={paciente_id}")
            return alertas
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching alertas: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching alertas: {e}")
            raise
    
    async def get_plano_cuidado(
        self, 
        plano_id: str
    ) -> PlanoCuidadoResponse:
        """
        Busca plano de cuidado por ID.
        
        Args:
            plano_id: ID do plano de cuidado
            
        Returns:
            Plano de cuidado
        """
        try:
            logger.debug(f"Fetching plano_cuidado for plano_id={plano_id}")
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/plano-cuidado/{plano_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            plano = PlanoCuidadoResponse(**data)
            
            logger.info(f"Found plano_cuidado: plano_id={plano_id}")
            return plano
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching plano_cuidado: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching plano_cuidado: {e}")
            raise

