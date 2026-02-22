"""Ecosystem event consumer — reads Redis Streams with XREADGROUP (EF-W006)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from wanda.events.coordinator import EventCoordinator
from wanda.events.models import IntelliCareEvent

logger = logging.getLogger(__name__)

# Redis streams to consume
INTELLICARE_STREAMS = [
    "intellicare:events:lab",
    "intellicare:events:vitals",
    "intellicare:events:adherence",
    "intellicare:events:conditions",
]

_BLOCK_MS = 5000      # XREADGROUP block timeout
_BATCH_SIZE = 10      # messages per read
_RETRY_DELAY = 5.0    # seconds between retries on error


class EcosystemEventConsumer:
    """Consumes IntelliCare Redis Streams using XREADGROUP.

    Runs in background and delegates each event to EventCoordinator.
    Gracefully no-ops when Redis is unavailable.
    """

    def __init__(
        self,
        redis_client: Optional[Any],
        coordinator: EventCoordinator,
        group: str = "wanda",
        consumer_name: str = "wanda-orchestrator",
    ) -> None:
        self._redis = redis_client
        self._coordinator = coordinator
        self._group = group
        self._consumer_name = consumer_name
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._processed = 0
        self._errors = 0
        self._started_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start_consuming(self) -> None:
        if self._redis is None:
            logger.warning("EcosystemEventConsumer: no Redis — consumer disabled")
            return
        if self._running:
            return
        await self._ensure_consumer_groups()
        self._running = True
        self._started_at = datetime.now(timezone.utc)
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("EcosystemEventConsumer started (group=%s)", self._group)

    async def stop_consuming(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("EcosystemEventConsumer stopped (processed=%d)", self._processed)

    # ------------------------------------------------------------------
    # Consumer group setup
    # ------------------------------------------------------------------

    async def _ensure_consumer_groups(self) -> None:
        for stream in INTELLICARE_STREAMS:
            try:
                await self._redis.xgroup_create(
                    stream, self._group, id="0", mkstream=True
                )
                logger.debug("Consumer group '%s' created for stream %s", self._group, stream)
            except Exception:
                # Group already exists — OK
                pass

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _consume_loop(self) -> None:
        streams_arg = {s: ">" for s in INTELLICARE_STREAMS}

        while self._running:
            try:
                messages = await self._redis.xreadgroup(
                    groupname=self._group,
                    consumername=self._consumer_name,
                    streams=streams_arg,
                    count=_BATCH_SIZE,
                    block=_BLOCK_MS,
                )
                if messages:
                    for stream_name, entries in messages:
                        for msg_id, data in entries:
                            await self._handle_message(stream_name, msg_id, data)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self._errors += 1
                logger.error("Consumer loop error: %s — retrying in %ss", exc, _RETRY_DELAY)
                await asyncio.sleep(_RETRY_DELAY)

    async def _handle_message(
        self,
        stream: str,
        msg_id: Any,
        data: dict[str, Any],
    ) -> None:
        try:
            event = self._parse_event(stream, data)
            result = await self._coordinator.coordinate(event)
            logger.debug(
                "Event %s coordinated: status=%s agents=%s",
                event.event_id, result.status, result.agents_notified,
            )
            # Acknowledge the message
            await self._redis.xack(stream, self._group, msg_id)
            self._processed += 1
        except Exception as exc:
            self._errors += 1
            logger.error("Failed to handle message %s from %s: %s", msg_id, stream, exc)

    @staticmethod
    def _parse_event(stream: str, data: dict[str, Any]) -> IntelliCareEvent:
        """Build an IntelliCareEvent from Redis Stream message data."""
        # Event type defaults based on stream name
        stream_defaults: dict[str, str] = {
            "intellicare:events:lab": "lab_result_critical",
            "intellicare:events:vitals": "vital_sign_alert",
            "intellicare:events:adherence": "adherence_missed",
            "intellicare:events:conditions": "condition_worsened",
        }
        event_type = data.get("event_type") or stream_defaults.get(stream, "unknown")
        import json  # noqa: PLC0415

        payload_raw = data.get("payload", "{}")
        try:
            payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        except (TypeError, ValueError):
            payload = {}

        return IntelliCareEvent(
            event_type=event_type,
            patient_id=data.get("patient_id", "unknown"),
            source_module=data.get("source_module", "unknown"),
            payload=payload,
            event_id=data.get("event_id", ""),
            priority=data.get("priority", "medium"),
        )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "group": self._group,
            "consumer": self._consumer_name,
            "streams": INTELLICARE_STREAMS,
            "processed": self._processed,
            "errors": self._errors,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }
