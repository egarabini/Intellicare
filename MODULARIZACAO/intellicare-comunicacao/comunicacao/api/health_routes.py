"""Endpoints de health check."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.monitoring.health import (
    ComponentHealth,
    HealthCheckService,
    ServiceHealth,
)
from comunicacao.storage.repository import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["health"])


def get_health_service(
    db: AsyncSession = Depends(get_db_session),
) -> HealthCheckService:
    """Dependency para obter HealthCheckService."""
    # TODO: Injetar Redis client quando disponível
    return HealthCheckService(db_session=db, redis_client=None)


@router.get("", response_model=ServiceHealth, summary="Health check geral")
async def get_overall_health(
    service: HealthCheckService = Depends(get_health_service),
) -> ServiceHealth:
    """
    Verifica health geral do serviço.
    
    Retorna:
    - status: healthy, degraded ou unhealthy
    - uptime_seconds: tempo de uptime do serviço
    - components: lista de health de cada componente
    
    Componentes verificados:
    - database: PostgreSQL
    - redis: Redis
    - channel_rocketchat: Dispatcher Rocket.Chat
    - channel_email: Dispatcher Email
    - channel_sms: Dispatcher SMS
    - channel_whatsapp: Dispatcher WhatsApp
    - channel_push: Dispatcher Push
    - channel_jitsi: Dispatcher Jitsi
    """
    health = await service.check_overall_health()
    return health


@router.get("/db", response_model=ComponentHealth, summary="Health check do banco de dados")
async def get_database_health(
    service: HealthCheckService = Depends(get_health_service),
) -> ComponentHealth:
    """
    Verifica health do PostgreSQL.
    
    Retorna:
    - status: healthy ou unhealthy
    - latency_ms: latência da query de health check
    - message: mensagem descritiva
    """
    health = await service.check_database()
    
    if health.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health.message,
        )
    
    return health


@router.get("/redis", response_model=ComponentHealth, summary="Health check do Redis")
async def get_redis_health(
    service: HealthCheckService = Depends(get_health_service),
) -> ComponentHealth:
    """
    Verifica health do Redis.
    
    Retorna:
    - status: healthy ou unhealthy
    - latency_ms: latência do PING
    - message: mensagem descritiva
    """
    health = await service.check_redis()
    
    if health.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health.message,
        )
    
    return health


@router.get("/channels", response_model=list[ComponentHealth], summary="Health check de todos os canais")
async def get_all_channels_health(
    service: HealthCheckService = Depends(get_health_service),
) -> list[ComponentHealth]:
    """
    Verifica health de todos os dispatchers de canal.
    
    Retorna lista de health para cada canal:
    - rocketchat
    - email
    - sms
    - whatsapp
    - push
    - jitsi
    """
    channels_health = await service.check_all_channels()
    return channels_health


@router.get("/channels/{channel}", response_model=ComponentHealth, summary="Health check de um canal específico")
async def get_channel_health(
    channel: str,
    service: HealthCheckService = Depends(get_health_service),
) -> ComponentHealth:
    """
    Verifica health de um canal específico.
    
    Args:
        channel: Nome do canal (rocketchat, email, sms, whatsapp, push, jitsi)
    
    Retorna:
    - status: healthy ou unhealthy
    - latency_ms: latência do health check
    - message: mensagem descritiva
    """
    health = await service.check_channel(channel, service._dispatcher_manager)
    
    if health.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health.message,
        )
    
    return health


@router.get("/liveness", summary="Liveness probe (Kubernetes)")
async def liveness_probe() -> dict[str, str]:
    """
    Liveness probe para Kubernetes.
    
    Retorna sempre 200 OK se o processo está rodando.
    Não verifica dependências externas.
    """
    return {"status": "alive"}


@router.get("/readiness", summary="Readiness probe (Kubernetes)")
async def readiness_probe(
    service: HealthCheckService = Depends(get_health_service),
) -> dict[str, str]:
    """
    Readiness probe para Kubernetes.
    
    Verifica se o serviço está pronto para receber tráfego.
    Retorna 503 se algum componente crítico está unhealthy.
    """
    health = await service.check_overall_health()
    
    # Componentes críticos: database, redis
    critical_components = ["database", "redis"]
    
    for component in health.components:
        if component.name in critical_components and component.status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Critical component {component.name} is unhealthy",
            )
    
    return {"status": "ready"}

