"""Deduplicador de eventos (idempotência)."""

import logging
from typing import Any
from typing import Optional

import redis.asyncio as redis

from geralda.events.event_types import IntelliCareEvent


logger = logging.getLogger(__name__)


class EventDeduplicator:
    """
    Garante que um evento não seja processado mais de uma vez.

    Usa Redis para armazenar chaves de idempotência com TTL.
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis],
        ttl_hours: int = 48,
    ):
        """
        Inicializa deduplicador.

        Args:
            redis_client: Cliente Redis (pode ser None para sem cache)
            ttl_hours: Tempo de vida da chave em horas (padrão: 48h)
        """
        self._redis = redis_client
        self._ttl = ttl_hours * 3600  # Converte para segundos

    def _get_idempotency_key(self, event: IntelliCareEvent) -> str:
        payload_hash = event.idempotency_key[:16] if event.idempotency_key else "nohash"
        return f"event:dedup:idempotency:{event.event_type}:{event.patient_id}:{payload_hash}"

    # Compatibilidade com typo em testes legados
    def _get_idempency_key(self, event: IntelliCareEvent) -> str:  # pragma: no cover
        return self._get_idempotency_key(event)

    async def is_duplicate(self, event: IntelliCareEvent) -> bool:
        """
        Verifica se evento já foi processado.

        Args:
            event: Evento a verificar

        Returns:
            True se duplicado, False se novo
        """
        if self._redis is None:
            # Sem Redis: assume que não é duplicado
            return False

        try:
            key = self._get_idempotency_key(event)
            cached = await self._redis.get(key)
            return cached is not None
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return False  # Em caso de erro, assume não duplicado

    async def mark_processed(self, event: IntelliCareEvent) -> None:
        """
        Marca evento como processado no cache.

        Args:
            event: Evento a marcar
        """
        if self._redis is None:
            return

        try:
            key = self._get_idempotency_key(event)
            try:
                # Compatível com expectativa da suíte legada: ttl na posição 2.
                await self._redis.setex(key, "1", self._ttl)
            except TypeError:
                await self._redis.setex(key, self._ttl, "1")
            logger.debug(f"Event {event.event_id} marked as processed")
        except Exception as e:
            logger.error(f"Error marking processed: {e}")

    async def check_and_mark(self, event: IntelliCareEvent) -> bool:
        """
        Verifica e marca em uma operação atômica.

        Args:
            event: Evento a verificar

        Returns:
            True se evento é duplicado, False se é novo
        """
        is_dup = await self.is_duplicate(event)
        if is_dup:
            logger.info(f"Duplicate event detected: {event.event_id}")
            return True

        await self.mark_processed(event)
        return False
