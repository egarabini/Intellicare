"""
Synchronous event publisher wrapper for donabedian.

Wraps intellicare_core.events.EventPublisher to provide a sync callback
for use in OperationalDataAccess.

Example:
    from donabedian.events import EventPublisher
    
    publisher = EventPublisher("redis://localhost:6379")
    
    # Sync callback for OperationalDataAccess
    def event_callback(operation: str, entity_type: str, entity_id: str, details: dict):
        publisher.publish_sync(
            event_type=f"{entity_type}.{operation.lower()}",
            data={
                "entity_id": str(entity_id),
                "entity_type": entity_type,
                "operation": operation,
                **details
            }
        )
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Synchronous wrapper around intellicare_core EventPublisher.
    
    Publishes CREATE/UPDATE/DELETE events to Redis Streams for consolidation.
    """

    def __init__(
        self,
        redis_url: str,
        stream_prefix: str = "intellicare",
        module_name: str = "donabedian"
    ):
        """
        Initialize event publisher.
        
        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379")
            stream_prefix: Prefix for stream names (default: "intellicare")
            module_name: Module name for event metadata
        """
        self.redis_url = redis_url
        self.stream_prefix = stream_prefix
        self.module_name = module_name
        self._redis: Any = None

    def _get_redis_sync(self) -> Any:
        """Get or initialize Redis connection (blocking)."""
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                self._redis.ping()
                logger.info(f"Connected to Redis: {self.redis_url}")
            except ImportError:
                raise RuntimeError(
                    "Redis not installed. Install with: pip install redis"
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis = None
                raise
        return self._redis

    def publish_sync(
        self,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        operation: str,
        data: Optional[dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Publish an event to Redis Streams (synchronous).

        Args:
            event_type: Type of event (e.g., "pilar.created")
            entity_type: Type of entity (e.g., "Pilar", "Indicator")
            entity_id: ID of the entity
            operation: Operation type (CREATE, UPDATE, DELETE)
            data: Additional event data

        Returns:
            Event ID from Redis, or None if publishing fails
        """
        try:
            if not data:
                data = {}

            redis = self._get_redis_sync()
            stream_name = f"{self.stream_prefix}:donabedian:{event_type}"

            # Build event message
            message = {
                "type": event_type,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "operation": operation,
                "module": self.module_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": json.dumps(data, default=str),
            }

            # Publish to Redis Stream
            result = redis.xadd(stream_name, message)

            logger.info(
                f"✅ Published event: {event_type} ({operation}) "
                f"entity={entity_id} stream={stream_name} msg_id={result}"
            )

            return result

        except Exception as e:
            logger.error(
                f"❌ Failed to publish event {event_type}: {e}",
                exc_info=True
            )
            return None

    def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            try:
                self._redis.close()
                logger.info("Closed Redis connection")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")
            finally:
                self._redis = None


# Global publisher instance (lazy-initialized)
_publisher: Optional[EventPublisher] = None


def get_event_publisher(
    redis_url: Optional[str] = None,
    stream_prefix: str = "intellicare",
    module_name: str = "donabedian"
) -> EventPublisher:
    """
    Get or create the global event publisher instance.

    Args:
        redis_url: Redis URL (uses env var REDIS_URL if not provided)
        stream_prefix: Prefix for stream names
        module_name: Module name

    Returns:
        EventPublisher instance
    """
    global _publisher

    if _publisher is None:
        if redis_url is None:
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        _publisher = EventPublisher(
            redis_url=redis_url,
            stream_prefix=stream_prefix,
            module_name=module_name
        )

    return _publisher


def get_event_callback(publisher: Optional[EventPublisher] = None):
    """
    Create a callback function for OperationalDataAccess.

    Args:
        publisher: EventPublisher instance (uses global if not provided)

    Returns:
        Callback function: (operation, entity_type, entity_id, details) -> None
    """
    if publisher is None:
        publisher = get_event_publisher()

    def callback(
        operation: str,
        entity_type: str,
        entity_id: str,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Callback for OperationalDataAccess to publish events.

        Args:
            operation: Operation type (CREATE, UPDATE, DELETE)
            entity_type: Type of entity
            entity_id: ID of entity
            details: Additional details
        """
        if details is None:
            details = {}

        # Convert event_type to lowercase
        event_type = f"{entity_type.lower()}.{operation.lower()}"

        # Publish event
        publisher.publish_sync(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            data=details
        )

    return callback
