"""Middleware HTTP para coleta de métricas."""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from comunicacao.monitoring.metrics import CommunicationMetrics

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware para coletar métricas de requisições HTTP.
    
    Coleta:
    - comm_api_request_duration_seconds: latência de cada requisição
    - Labels: method, endpoint, status_code
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa requisição e coleta métricas."""
        # Ignorar endpoint de métricas
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Medir latência
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calcular latência
            latency = time.time() - start_time
            
            # Extrair endpoint (remover query params)
            endpoint = request.url.path
            
            # Registrar métrica
            CommunicationMetrics.api_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).observe(latency)
            
            logger.debug(
                "HTTP %s %s -> %d (%.3fs)",
                request.method,
                endpoint,
                response.status_code,
                latency,
            )
            
            return response
        
        except Exception as exc:
            # Calcular latência mesmo em caso de erro
            latency = time.time() - start_time
            
            # Registrar métrica com status 500
            CommunicationMetrics.api_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
            ).observe(latency)
            
            logger.error(
                "HTTP %s %s -> ERROR (%.3fs): %s",
                request.method,
                request.url.path,
                latency,
                exc,
            )
            
            raise


class DBConnectionMetricsCollector:
    """Coletor de métricas de conexões do banco de dados."""
    
    def __init__(self, engine: Any):
        """
        Inicializa coletor.
        
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
    
    def collect_metrics(self) -> None:
        """Coleta métricas de conexões do pool."""
        try:
            pool = self.engine.pool
            
            # Conexões ativas
            active_connections = pool.checkedout()
            CommunicationMetrics.db_connections_active.set(active_connections)
            
            logger.debug("DB connections: %d active", active_connections)
        
        except Exception as exc:
            logger.error("Failed to collect DB connection metrics: %s", exc)


class RedisConnectionMetricsCollector:
    """Coletor de métricas de conexões do Redis."""
    
    def __init__(self, redis_client: Any):
        """
        Inicializa coletor.
        
        Args:
            redis_client: Redis client
        """
        self.redis_client = redis_client
    
    async def collect_metrics(self) -> None:
        """Coleta métricas de conexões do Redis."""
        try:
            # Obter info do Redis
            info = await self.redis_client.info("clients")
            
            # Conexões ativas
            connected_clients = info.get("connected_clients", 0)
            CommunicationMetrics.redis_connections_active.set(connected_clients)
            
            logger.debug("Redis connections: %d active", connected_clients)
        
        except Exception as exc:
            logger.error("Failed to collect Redis connection metrics: %s", exc)


class ChannelHealthMetricsCollector:
    """Coletor de métricas de health dos dispatchers."""
    
    def __init__(self, dispatcher_manager: Any):
        """
        Inicializa coletor.
        
        Args:
            dispatcher_manager: DispatcherManager
        """
        self.dispatcher_manager = dispatcher_manager
    
    async def collect_metrics(self) -> None:
        """Coleta métricas de health dos dispatchers."""
        channels = ["rocketchat", "email", "sms", "whatsapp", "push", "jitsi"]
        
        for channel in channels:
            try:
                dispatcher = self.dispatcher_manager.get_dispatcher(channel)
                if not dispatcher:
                    CommunicationMetrics.dispatcher_health.labels(channel=channel).set(0)
                    continue
                
                # Executar health check
                health = await dispatcher.health_check()
                
                # Atualizar métrica
                CommunicationMetrics.dispatcher_health.labels(channel=channel).set(
                    1 if health.available else 0
                )
                
                logger.debug("Channel %s health: %s", channel, "healthy" if health.available else "unhealthy")
            
            except Exception as exc:
                logger.error("Failed to collect health for channel %s: %s", channel, exc)
                CommunicationMetrics.dispatcher_health.labels(channel=channel).set(0)

