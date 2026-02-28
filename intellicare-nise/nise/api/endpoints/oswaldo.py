"""Endpoints para integração com Oswaldo."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from nise.services.oswaldo_client import (
    OswaldoClient,
    DiagnosticoResponse,
    AlertaResponse,
    ResumoPacienteResponse
)
from nise.services.cache import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oswaldo", tags=["oswaldo"])


# ── Dependencies ──────────────────────────────────────────────────


def get_oswaldo_client() -> OswaldoClient:
    """Dependency para obter cliente Oswaldo."""
    # TODO: Obter base_url de config
    return OswaldoClient(base_url="http://localhost:8002")


def get_cache_service() -> CacheService:
    """Dependency para obter serviço de cache."""
    # TODO: Obter redis_url de config
    return CacheService(redis_url="redis://localhost:6379/0", default_ttl=300)


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("/paciente/{paciente_id}/resumo", response_model=ResumoPacienteResponse)
async def get_resumo_paciente(
    paciente_id: str,
    use_cache: bool = Query(True, description="Usar cache Redis"),
    oswaldo: OswaldoClient = Depends(get_oswaldo_client),
    cache: CacheService = Depends(get_cache_service)
):
    """
    Endpoint para chatbot consultar resumo do paciente.
    
    Retorna:
    - Diagnósticos ativos
    - Alertas críticos
    - Plano de cuidado atual
    - Risco Framingham (futuro)
    
    Args:
        paciente_id: ID do paciente
        use_cache: Se True, tenta buscar do cache primeiro
        oswaldo: Cliente Oswaldo (injetado)
        cache: Serviço de cache (injetado)
        
    Returns:
        ResumoPacienteResponse com dados consolidados
        
    Raises:
        HTTPException: Se paciente não encontrado ou erro na API
    """
    try:
        # Tentar cache primeiro (TTL 5 min)
        cache_key = f"paciente_resumo:{paciente_id}"
        
        if use_cache:
            cached = await cache.get(cache_key)
            if cached:
                logger.info(f"Cache HIT for paciente_id={paciente_id}")
                return ResumoPacienteResponse(**cached)
        
        logger.info(f"Fetching resumo for paciente_id={paciente_id} from Oswaldo API")
        
        # Buscar dados do Oswaldo
        diagnosticos = await oswaldo.get_diagnosticos(paciente_id)
        alertas = await oswaldo.get_alertas(paciente_id, status="ativo")
        
        # Buscar plano de cuidado se houver diagnóstico
        plano_cuidado_atual = None
        if diagnosticos and diagnosticos[0].plano_cuidado_id:
            try:
                plano_cuidado_atual = await oswaldo.get_plano_cuidado(
                    diagnosticos[0].plano_cuidado_id
                )
            except Exception as e:
                logger.warning(f"Error fetching plano_cuidado: {e}")
        
        # Montar resumo
        resumo = ResumoPacienteResponse(
            paciente_id=paciente_id,
            diagnosticos=diagnosticos,
            alertas_criticos=[
                a.mensagem for a in alertas if a.tipo == "critico"
            ],
            total_alertas=len(alertas),
            plano_cuidado_atual=plano_cuidado_atual,
            risco_framingham=None  # TODO: Implementar Framingham
        )
        
        # Cachear por 5 minutos
        if use_cache:
            await cache.set(cache_key, resumo.model_dump(), ttl=300)
            logger.debug(f"Cached resumo for paciente_id={paciente_id}")
        
        logger.info(f"Successfully fetched resumo for paciente_id={paciente_id}")
        return resumo
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resumo for paciente_id={paciente_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar resumo do paciente: {str(e)}"
        )
    finally:
        await oswaldo.close()
        await cache.close()


@router.get("/paciente/{paciente_id}/diagnosticos", response_model=list[DiagnosticoResponse])
async def get_diagnosticos(
    paciente_id: str,
    oswaldo: OswaldoClient = Depends(get_oswaldo_client)
):
    """
    Busca diagnósticos do paciente.
    
    Args:
        paciente_id: ID do paciente
        oswaldo: Cliente Oswaldo (injetado)
        
    Returns:
        Lista de diagnósticos
    """
    try:
        diagnosticos = await oswaldo.get_diagnosticos(paciente_id)
        return diagnosticos
    except Exception as e:
        logger.error(f"Error fetching diagnosticos: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await oswaldo.close()


@router.get("/paciente/{paciente_id}/alertas", response_model=list[AlertaResponse])
async def get_alertas(
    paciente_id: str,
    status: str = Query("ativo", description="Status dos alertas"),
    oswaldo: OswaldoClient = Depends(get_oswaldo_client)
):
    """
    Busca alertas do paciente.
    
    Args:
        paciente_id: ID do paciente
        status: Status dos alertas ("ativo", "resolvido", "todos")
        oswaldo: Cliente Oswaldo (injetado)
        
    Returns:
        Lista de alertas
    """
    try:
        alertas = await oswaldo.get_alertas(paciente_id, status=status)
        return alertas
    except Exception as e:
        logger.error(f"Error fetching alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await oswaldo.close()

