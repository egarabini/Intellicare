"""Publicador de eventos via Redis Streams.

Modulos publicam eventos para que outros modulos (ou Wanda) possam reagir.
Este componente e OPCIONAL — so funciona se redis estiver instalado.

Exemplo:
    publisher = EventPublisher("redis://localhost:6379")
    await publisher.publish("alert.created", {
        "module": "intellicare-oswaldo",
        "patient_id": "123",
        "severity": "urgent",
        "message": "eGFR em queda rapida",
    })
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publica eventos em Redis Streams para comunicacao entre modulos."""

    def __init__(self, redis_url: str, stream_prefix: str = "intellicare") -> None:
        self.redis_url = redis_url
        self.stream_prefix = stream_prefix
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        if self._redis is None:
            try:
                import redis.asyncio as aioredis

                self._redis = aioredis.from_url(self.redis_url)
            except ImportError:
                raise RuntimeError(
                    "Redis nao instalado. Instale com: pip install intellicare-core[events]"
                )
        return self._redis

    async def publish(self, event_type: str, data: dict[str, Any]) -> str | None:
        """Publica um evento no stream Redis.

        Args:
            event_type: Tipo do evento (ex: "alert.created", "analysis.completed")
            data: Dados do evento

        Returns:
            ID da mensagem no stream, ou None se falhar.
        """
        try:
            redis = await self._get_redis()
            stream_name = f"{self.stream_prefix}:{event_type}"
            message = {
                "type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": json.dumps(data, default=str),
            }
            result = await redis.xadd(stream_name, message)
            return result.decode() if isinstance(result, bytes) else str(result)
        except Exception as e:
            logger.warning("Falha ao publicar evento %s: %s", event_type, e)
            return None

    async def close(self) -> None:
        """Fecha conexao com Redis."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
