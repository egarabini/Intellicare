"""Publicador de eventos para consumidores."""

import logging
from typing import Optional

import httpx
import redis.asyncio as redis

from geralda.events.event_types import IntelliCareEvent


logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publica eventos para consumidores internos e externos.

    Usa Redis Streams para pub/sub e HTTP para notificar Wanda.
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        http_client: Optional[object] = None,
        wanda_max_retries: int = 1,
    ):
        """
        Inicializa publicador.

        Args:
            redis_client: Cliente Redis (opcional)
        """
        self._redis = redis_client
        self._http_client = http_client
        self._wanda_max_retries = wanda_max_retries

    def _get_stream_name(self, event: IntelliCareEvent) -> str:
        prefix = event.event_type.split(".")[0] if "." in event.event_type else "events"
        return f"intellicare:events:{prefix}"

    async def publish(self, event: IntelliCareEvent) -> None:
        """
        Publica evento no Redis Stream.

        Args:
            event: Evento a publicar
        """
        if self._redis is None:
            logger.warning("Redis not available, skipping publish")
            return

        try:
            stream_key = self._get_stream_name(event)

            # Serializar evento
            event_data = event.to_dict()

            # Publicar no stream
            await self._redis.xadd(
                stream_key,
                {
                    "event_type": event_data.get("event_type", ""),
                    "patient_id": event_data.get("patient_id", ""),
                    "timestamp": event_data.get("timestamp", ""),
                    "data": str(event_data),
                },
            )

            logger.debug(f"Event published to stream: {stream_key}")

        except Exception as e:
            logger.error(f"Error publishing event: {e}")

    async def publish_to_wanda(
        self,
        event: IntelliCareEvent,
        wanda_url: str = "http://localhost:8007",
    ) -> None:
        """
        Notifica Wanda sobre evento importante.

        Usa HTTP POST para Wanda /api/v1/events.

        Args:
            event: Evento a notificar
            wanda_url: URL base do Wanda
        """
        # Publicar apenas eventos importantes
        important_types = [
            "clinical.condition_worsened",
            "clinical.condition_diagnosed",
            "care.adherence_low",
            "care.task_missed",
        ]

        if event.event_type not in important_types:
            return

        if self._http_client is None:
            logger.warning("HTTP client not available, skipping Wanda notification")
            return

        url = wanda_url if wanda_url.endswith("/events") else f"{wanda_url}/api/v1/events"
        retries = max(self._wanda_max_retries, 1)

        for attempt in range(1, retries + 1):
            try:
                response = await self._http_client.post(url, json=event.to_dict())
                if getattr(response, "status_code", 500) == 200:
                    logger.info(f"Event notified to Wanda: {event.event_id}")
                    return
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Error notifying Wanda: {e}")
                    return


async def _unused_default_client_example() -> None:
    """Mantém import de httpx válido para fluxos externos fora dos testes."""
    async with httpx.AsyncClient(timeout=5.0):
        return
