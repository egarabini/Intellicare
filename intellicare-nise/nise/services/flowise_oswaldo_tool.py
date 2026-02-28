"""LangChain Tool para integração Flowise ↔ Oswaldo."""

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)


# ── Schemas ────────────────────────────────────────────────────────────────


class OswaldoDiagnosticoInput(BaseModel):
    """Input schema para buscar diagnósticos."""
    
    paciente_id: str = Field(
        description="ID do paciente para buscar diagnósticos (ex: 'pac-123')"
    )


class OswaldoAlertasInput(BaseModel):
    """Input schema para buscar alertas."""
    
    paciente_id: str = Field(
        description="ID do paciente para buscar alertas (ex: 'pac-123')"
    )
    status: Optional[str] = Field(
        default="ativo",
        description="Status dos alertas: 'ativo', 'resolvido', 'todos'"
    )


class OswaldoResumoInput(BaseModel):
    """Input schema para buscar resumo do paciente."""
    
    paciente_id: str = Field(
        description="ID do paciente para buscar resumo completo (ex: 'pac-123')"
    )


# ── Tools ──────────────────────────────────────────────────────────────────


class OswaldoDiagnosticoTool(BaseTool):
    """Tool para buscar diagnósticos de doenças crônicas do paciente."""
    
    name: str = "oswaldo_diagnostico"
    description: str = (
        "Busca diagnósticos de doenças crônicas (diabetes, hipertensão, DRC) "
        "de um paciente específico. Use quando o usuário perguntar sobre "
        "diagnósticos, condições, classificações ou estadiamento."
    )
    args_schema: Type[BaseModel] = OswaldoDiagnosticoInput
    
    nise_base_url: str = "http://localhost:8000"
    
    def _run(self, paciente_id: str) -> str:
        """Executa a busca de diagnósticos."""
        try:
            url = f"{self.nise_base_url}/api/v1/oswaldo/paciente/{paciente_id}/diagnosticos"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                
                diagnosticos = response.json()
                
                if not diagnosticos:
                    return f"Nenhum diagnóstico encontrado para o paciente {paciente_id}."
                
                # Formatar resposta
                resultado = f"Diagnósticos do paciente {paciente_id}:\n\n"
                
                for diag in diagnosticos:
                    resultado += f"• {diag['condicao'].upper()}\n"
                    resultado += f"  - Classificação: {diag['classificacao']}\n"
                    resultado += f"  - Estadiamento: {diag['estadiamento']}\n"
                    resultado += f"  - Data: {diag['data_diagnostico']}\n"
                    if diag.get('plano_cuidado_id'):
                        resultado += f"  - Plano de Cuidado: {diag['plano_cuidado_id']}\n"
                    resultado += "\n"
                
                return resultado
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            return f"Erro ao buscar diagnósticos: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Erro ao buscar diagnósticos: {str(e)}"
    
    async def _arun(self, paciente_id: str) -> str:
        """Versão async (não implementada)."""
        raise NotImplementedError("Async not implemented")


class OswaldoAlertasTool(BaseTool):
    """Tool para buscar alertas clínicos do paciente."""
    
    name: str = "oswaldo_alertas"
    description: str = (
        "Busca alertas clínicos (críticos, avisos) de um paciente específico. "
        "Use quando o usuário perguntar sobre alertas, avisos, problemas "
        "ou situações que requerem atenção."
    )
    args_schema: Type[BaseModel] = OswaldoAlertasInput
    
    nise_base_url: str = "http://localhost:8000"
    
    def _run(self, paciente_id: str, status: str = "ativo") -> str:
        """Executa a busca de alertas."""
        try:
            url = f"{self.nise_base_url}/api/v1/oswaldo/paciente/{paciente_id}/alertas"
            params = {"status": status}
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                alertas = response.json()
                
                if not alertas:
                    return f"Nenhum alerta {status} encontrado para o paciente {paciente_id}."
                
                # Formatar resposta
                resultado = f"Alertas {status} do paciente {paciente_id}:\n\n"
                
                for alerta in alertas:
                    emoji = "🔴" if alerta['tipo'] == "critico" else "🟡"
                    resultado += f"{emoji} {alerta['tipo'].upper()}\n"
                    resultado += f"  - Mensagem: {alerta['mensagem']}\n"
                    resultado += f"  - Data: {alerta['data_criacao']}\n"
                    resultado += f"  - Status: {alerta['status']}\n\n"
                
                return resultado
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            return f"Erro ao buscar alertas: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Erro ao buscar alertas: {str(e)}"
    
    async def _arun(self, paciente_id: str, status: str = "ativo") -> str:
        """Versão async (não implementada)."""
        raise NotImplementedError("Async not implemented")


class OswaldoResumoTool(BaseTool):
    """Tool para buscar resumo completo do paciente."""
    
    name: str = "oswaldo_resumo"
    description: str = (
        "Busca resumo completo do paciente incluindo diagnósticos, alertas "
        "críticos e plano de cuidado atual. Use quando o usuário pedir "
        "informações gerais ou resumo do paciente."
    )
    args_schema: Type[BaseModel] = OswaldoResumoInput
    
    nise_base_url: str = "http://localhost:8000"
    
    def _run(self, paciente_id: str) -> str:
        """Executa a busca de resumo."""
        try:
            url = f"{self.nise_base_url}/api/v1/oswaldo/paciente/{paciente_id}/resumo"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                
                resumo = response.json()
                
                # Formatar resposta
                resultado = f"📋 RESUMO DO PACIENTE {paciente_id}\n\n"
                
                # Diagnósticos
                if resumo.get('diagnosticos'):
                    resultado += "🏥 DIAGNÓSTICOS:\n"
                    for diag in resumo['diagnosticos']:
                        resultado += f"  • {diag['condicao']} - {diag['classificacao']} ({diag['estadiamento']})\n"
                    resultado += "\n"
                
                # Alertas críticos
                if resumo.get('alertas_criticos'):
                    resultado += "🔴 ALERTAS CRÍTICOS:\n"
                    for alerta in resumo['alertas_criticos']:
                        resultado += f"  • {alerta}\n"
                    resultado += "\n"
                
                # Total de alertas
                resultado += f"📊 Total de alertas: {resumo.get('total_alertas', 0)}\n\n"
                
                # Plano de cuidado
                if resumo.get('plano_cuidado_atual'):
                    resultado += f"📝 Plano de Cuidado: {resumo['plano_cuidado_atual']}\n"
                
                return resultado
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            return f"Erro ao buscar resumo: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Erro ao buscar resumo: {str(e)}"
    
    async def _arun(self, paciente_id: str) -> str:
        """Versão async (não implementada)."""
        raise NotImplementedError("Async not implemented")

