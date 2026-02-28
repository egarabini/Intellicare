"""Consumidor Redis Streams para eventos clinicos."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from comunicacao.config import ComunicacaoConfig

logger = logging.getLogger(__name__)


def build_clinical_alert_from_stream(
    fields: dict[str, Any],
    event_type_fallback: str = "alert.created",
) -> dict[str, Any] | None:
    """Converte payload de Redis Stream para formato ClinicalAlertEventRequest."""
    raw_data = fields.get("data")
    if not raw_data:
        return None

    try:
        data = json.loads(raw_data)
    except Exception:
        return None

    patient_id = data.get("patient_id")
    message = data.get("message")
    if not patient_id or not message:
        return None

    source_module = data.get("source_module") or data.get("module") or "unknown"
    alert_type = data.get("alert_type") or data.get("type") or event_type_fallback

    return {
        "patient_id": str(patient_id),
        "source_module": str(source_module),
        "alert_type": str(alert_type),
        "severity": str(data.get("severity") or "media"),
        "message": str(message),
        "room_id": data.get("room_id"),
        "correlation_id": data.get("correlation_id"),
    }


class RedisAlertConsumer:
    """Consome eventos Redis Streams e despacha alertas clinicos."""

    def __init__(
        self,
        config: ComunicacaoConfig,
        on_alert: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        self.config = config
        self.on_alert = on_alert
        self._task: asyncio.Task[None] | None = None

    def status(self) -> dict[str, Any]:
        running = self._task is not None and not self._task.done()
        stream_name = f"{self.config.event_stream_prefix}:{self.config.event_alert_type}"
        return {"ok": True, "running": running, "stream": stream_name}

    async def start(self) -> dict[str, Any]:
        if self._task is not None and not self._task.done():
            return {"ok": True, "running": True, "already_running": True}
        self._task = asyncio.create_task(self._run(), name="redis-alert-consumer")
        return {"ok": True, "running": True}

    async def stop(self) -> dict[str, Any]:
        if self._task is None or self._task.done():
            self._task = None
            return {"ok": True, "running": False}
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
        return {"ok": True, "running": False}

    async def _run(self) -> None:
        try:
            import redis.asyncio as aioredis
        except ImportError:
            logger.warning("redis nao instalado; consumidor de eventos desativado")
            return

        stream_name = f"{self.config.event_stream_prefix}:{self.config.event_alert_type}"
        last_id = "$"
        redis = aioredis.from_url(self.config.redis_url, decode_responses=True)
        logger.info("Consumidor Redis iniciado no stream: %s", stream_name)
        try:
            while True:
                result = await redis.xread(
                    streams={stream_name: last_id},
                    count=20,
                    block=self.config.event_poll_timeout_ms,
                )
                if not result:
                    continue
                for _, messages in result:
                    for message_id, fields in messages:
                        last_id = message_id
                        payload = build_clinical_alert_from_stream(
                            fields=fields,
                            event_type_fallback=self.config.event_alert_type,
                        )
                        if not payload:
                            continue
                        # Adicionar event_id do Redis Stream ao payload
                        payload["event_id"] = message_id
                        try:
                            await self.on_alert(payload)
                        except Exception as exc:  # pragma: no cover - runtime guard
                            logger.warning("Falha ao processar evento %s: %s", message_id, exc)
        except asyncio.CancelledError:
            raise
        finally:
            await redis.close()
            logger.info("Consumidor Redis finalizado")
