"""HL7v2 Event Publisher — Publish HL7v2 events to Redis Streams.

This module publishes events when HL7v2 messages are processed and FHIR resources are created.
Events are published to Redis Streams for consumption by WANDA, Geralda, and other modules.

Streams:
- intellicare:hl7v2:patient-created
- intellicare:hl7v2:encounter-created

Event Format:
{
    "event_type": "patient.created",
    "resource_type": "Patient",
    "resource_id": "patient-123",
    "source_system": "HOSPITAL:FACILITY",
    "message_control_id": "MSG00001",
    "timestamp": "2026-02-24T10:00:00Z"
}

References:
- IntelliCare Event Publisher: intellicare-core/intellicare_core/events/publisher.py
- Oswaldo Event Publisher: intellicare-oswaldo/docs/specs/fase-03-integracao-eventos/EF-O009_EVENTOS_REDIS_STREAM.md
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    class _RedisStub:
        @staticmethod
        async def from_url(*args, **kwargs):
            raise ImportError("redis.asyncio is not installed")

    aioredis = _RedisStub()  # type: ignore[assignment]
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class HL7v2EventPublisher:
    """Publish HL7v2 events to Redis Streams.

    Events are published when HL7v2 messages are processed and FHIR resources are created.
    This allows other modules (WANDA, Geralda) to react to new patients and encounters.
    """

    STREAM_PREFIX = "intellicare:hl7v2"
    MAX_STREAM_LENGTH = 10_000  # FIFO, removes oldest when exceeded
    PUBLISH_TIMEOUT_S = 2.0  # Don't block main flow

    def __init__(self, redis_url: str):
        """Initialize the event publisher.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379")
        """
        self._redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis.

        This should be called during application startup.
        """
        if not REDIS_AVAILABLE:
            logger.warning("redis-asyncio not installed, events will not be published")
            return

        try:
            self._redis = await aioredis.from_url(
                self._redis_url,
                decode_responses=True,
            )
            logger.info(f"✅ HL7v2 Event Publisher connected to Redis: {self._redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self._redis = None

    async def disconnect(self) -> None:
        """Disconnect from Redis.

        This should be called during application shutdown.
        """
        if self._redis:
            await self._redis.close()
            logger.info("HL7v2 Event Publisher disconnected from Redis")

    async def publish_patient_created(
        self,
        patient: dict,
        source_system: str,
        message_control_id: str,
    ) -> bool:
        """Publish patient-created event.

        Args:
            patient: FHIR Patient resource (dict)
            source_system: Source system identifier (e.g., "HOSPITAL:FACILITY")
            message_control_id: HL7v2 message control ID (MSH-10)

        Returns:
            True if published successfully, False otherwise
        """
        event = {
            "event_type": "patient.created",
            "resource_type": "Patient",
            "resource_id": patient.get("id", "unknown"),
            "source_system": source_system,
            "message_control_id": message_control_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return await self._publish("patient-created", event)

    async def publish_encounter_created(
        self,
        encounter: dict,
        patient_id: str,
        source_system: str,
        message_control_id: str,
    ) -> bool:
        """Publish encounter-created event.

        Args:
            encounter: FHIR Encounter resource (dict)
            patient_id: Patient ID (from Encounter.subject.reference)
            source_system: Source system identifier (e.g., "HOSPITAL:FACILITY")
            message_control_id: HL7v2 message control ID (MSH-10)

        Returns:
            True if published successfully, False otherwise
        """
        event = {
            "event_type": "encounter.created",
            "resource_type": "Encounter",
            "resource_id": encounter.get("id", "unknown"),
            "patient_id": patient_id,
            "source_system": source_system,
            "message_control_id": message_control_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return await self._publish("encounter-created", event)

    async def _publish(self, event_name: str, event_data: dict[str, Any]) -> bool:
        """Publish event to Redis Stream.

        Args:
            event_name: Event name (e.g., "patient-created")
            event_data: Event data dictionary

        Returns:
            True if published successfully, False otherwise
        """
        if not self._redis:
            logger.warning(f"Redis not connected, skipping event: {event_name}")
            return False

        try:
            stream_name = f"{self.STREAM_PREFIX}:{event_name}"

            # Publish to Redis Stream with timeout
            await asyncio.wait_for(
                self._redis.xadd(
                    stream_name,
                    event_data,
                    maxlen=self.MAX_STREAM_LENGTH,
                ),
                timeout=self.PUBLISH_TIMEOUT_S,
            )

            logger.info(f"✅ Published event: {event_name} → {stream_name}")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout publishing event: {event_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to publish event {event_name}: {e}")
            return False
