"""Serviço de health checks."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.monitoring.config import MonitoringConfig

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Status de health check."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ComponentHealth(BaseModel):
    """Health de um componente individual."""
    name: str
    status: HealthStatus
    message: str | None = None
    latency_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceHealth(BaseModel):
    """Health geral do serviço."""
    status: HealthStatus
    version: str = "1.0.0"
    uptime_seconds: float
    components: list[ComponentHealth]
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthCheckService:
    """Serviço de health checks para todos os componentes."""
    
    def __init__(
        self,
        config: MonitoringConfig | None = None,
        db_session: AsyncSession | None = None,
        redis_client: Any | None = None,
        dispatcher_manager: Any | None = None,
    ):
        self.config = config or MonitoringConfig.from_env()
        self._db_session = db_session
        self._redis_client = redis_client
        self._dispatcher_manager = dispatcher_manager
        self._start_time = time.time()
        self._channel_health_cache: dict[str, tuple[ComponentHealth, float]] = {}
    
    async def check_overall_health(self) -> ServiceHealth:
        """Verifica health geral do serviço."""
        components: list[ComponentHealth] = []
        
        # Check database
        if self._db_session:
            db_health = await self.check_database()
            components.append(db_health)
        
        # Check Redis
        if self._redis_client:
            redis_health = await self.check_redis()
            components.append(redis_health)
        
        # Check channels
        channels_health = await self.check_all_channels()
        components.extend(channels_health)
        
        # Determinar status geral
        statuses = [c.status for c in components]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.DEGRADED
        
        uptime = time.time() - self._start_time
        
        return ServiceHealth(
            status=overall_status,
            uptime_seconds=uptime,
            components=components,
        )
    
    async def check_database(self) -> ComponentHealth:
        """Verifica health do PostgreSQL."""
        if not self._db_session:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNKNOWN,
                message="DB session not configured",
            )
        
        start_time = time.time()
        try:
            # Executar query simples
            result = await asyncio.wait_for(
                self._db_session.execute(text(self.config.db_health_query)),
                timeout=self.config.db_health_timeout_seconds,
            )
            await result.close()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="PostgreSQL connection OK",
                latency_ms=latency_ms,
            )
        
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database timeout after {self.config.db_health_timeout_seconds}s",
                latency_ms=latency_ms,
            )
        
        except Exception as exc:
            latency_ms = (time.time() - start_time) * 1000
            logger.error("Database health check failed: %s", exc)
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {type(exc).__name__}",
                latency_ms=latency_ms,
                details={"error": str(exc)},
            )
    
    async def check_redis(self) -> ComponentHealth:
        """Verifica health do Redis."""
        if not self._redis_client:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNKNOWN,
                message="Redis client not configured",
            )
        
        start_time = time.time()
        try:
            # Executar PING
            await asyncio.wait_for(
                self._redis_client.ping(),
                timeout=self.config.redis_health_timeout_seconds,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connection OK",
                latency_ms=latency_ms,
            )
        
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis timeout after {self.config.redis_health_timeout_seconds}s",
                latency_ms=latency_ms,
            )
        
        except Exception as exc:
            latency_ms = (time.time() - start_time) * 1000
            logger.error("Redis health check failed: %s", exc)
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis error: {type(exc).__name__}",
                latency_ms=latency_ms,
                details={"error": str(exc)},
            )

    async def check_all_channels(self) -> list[ComponentHealth]:
        """Verifica health de todos os dispatchers de canal."""
        manager = self._dispatcher_manager
        if manager is None:
            return []
        channels = list(manager.list_channels()) if hasattr(manager, "list_channels") else ["rocketchat", "email", "sms", "whatsapp", "push", "jitsi"]

        results: list[ComponentHealth] = []

        for channel in channels:
            # Verificar cache
            cached = self._channel_health_cache.get(channel)
            if cached:
                cached_health, cached_time = cached
                if time.time() - cached_time < self.config.channel_health_cache_ttl_seconds:
                    results.append(cached_health)
                    continue

            # Executar health check
            health = await self.check_channel(channel, manager)

            # Atualizar cache
            self._channel_health_cache[channel] = (health, time.time())

            results.append(health)

        return results

    async def check_channel(self, channel: str, manager: Any) -> ComponentHealth:
        """Verifica health de um canal específico."""
        start_time = time.time()

        try:
            dispatcher = manager.get_dispatcher(channel)
            if not dispatcher:
                return ComponentHealth(
                    name=f"channel_{channel}",
                    status=HealthStatus.UNKNOWN,
                    message=f"Dispatcher {channel} not found",
                )

            # Executar health check do dispatcher
            health_result = await asyncio.wait_for(
                dispatcher.health_check(),
                timeout=self.config.channel_health_timeout_seconds,
            )

            latency_ms = (time.time() - start_time) * 1000

            # Converter status do dispatcher para HealthStatus
            if health_result.available:
                status = HealthStatus.HEALTHY
                message = f"{channel} dispatcher OK"
            else:
                status = HealthStatus.UNHEALTHY
                message = health_result.message or f"{channel} dispatcher unavailable"

            return ComponentHealth(
                name=f"channel_{channel}",
                status=status,
                message=message,
                latency_ms=latency_ms,
                details={
                    "available": health_result.available,
                    "latency_ms": health_result.latency_ms,
                },
            )

        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name=f"channel_{channel}",
                status=HealthStatus.UNHEALTHY,
                message=f"{channel} health check timeout",
                latency_ms=latency_ms,
            )

        except Exception as exc:
            latency_ms = (time.time() - start_time) * 1000
            logger.error("Channel %s health check failed: %s", channel, exc)
            return ComponentHealth(
                name=f"channel_{channel}",
                status=HealthStatus.UNHEALTHY,
                message=f"{channel} error: {type(exc).__name__}",
                latency_ms=latency_ms,
                details={"error": str(exc)},
            )

