"""
FASE 2.2: Event Publishing Tests

Tests that CREATE/UPDATE/DELETE operations publish events to Redis Streams.
"""

import json
import pytest
from uuid import uuid4
from datetime import datetime

# Import event publisher
from donabedian.events import EventPublisher, get_event_callback, get_event_publisher

# Try to import redis, skip tests if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not installed")
class TestEventPublishing:
    """Test event publishing to Redis Streams."""

    @pytest.fixture
    def redis_url(self) -> str:
        """Redis URL for testing."""
        return "redis://localhost:6379"

    @pytest.fixture
    def publisher(self, redis_url: str) -> EventPublisher:
        """Create event publisher."""
        pub = EventPublisher(redis_url=redis_url)
        yield pub
        # Cleanup
        pub.close()

    @pytest.fixture
    def redis_client(self, redis_url: str):
        """Create Redis client for reading events."""
        client = redis.from_url(redis_url, decode_responses=True)
        yield client
        # Cleanup: delete test streams
        for key in client.scan_iter("intellicare:donabedian:*"):
            client.delete(key)
        client.close()

    def test_publisher_connects_to_redis(self, publisher: EventPublisher):
        """Test that publisher can connect to Redis."""
        # Should not raise exception
        assert publisher._redis is None  # Lazy initialization
        redis_conn = publisher._get_redis_sync()
        assert redis_conn is not None

    def test_publish_pilar_create_event(
        self,
        publisher: EventPublisher,
        redis_client: redis.Redis
    ):
        """Test publishing a pilar.create event."""
        pilar_id = uuid4()
        entity_type = "Pilar"
        
        # Publish event
        event_id = publisher.publish_sync(
            event_type="pilar.create",
            entity_type=entity_type,
            entity_id=pilar_id,
            operation="CREATE",
            data={"nome": "Eficácia", "tipo": "ESTRUTURA"}
        )
        
        # Verify event was published
        assert event_id is not None
        
        # Read event from Redis Stream
        stream_name = "intellicare:donabedian:pilar.create"
        events = redis_client.xrange(stream_name, count=1)
        
        assert len(events) >= 1
        msg_id, msg_data = events[0]
        
        # Verify event content
        assert msg_data["type"] == "pilar.create"
        assert msg_data["entity_id"] == str(pilar_id)
        assert msg_data["entity_type"] == entity_type
        assert msg_data["operation"] == "CREATE"
        assert msg_data["module"] == "donabedian"
        
        # Verify data is JSON encoded
        data = json.loads(msg_data["data"])
        assert data["nome"] == "Eficácia"
        assert data["tipo"] == "ESTRUTURA"

    def test_publish_pilar_update_event(
        self,
        publisher: EventPublisher,
        redis_client: redis.Redis
    ):
        """Test publishing a pilar.update event."""
        pilar_id = uuid4()
        
        # Publish update event
        event_id = publisher.publish_sync(
            event_type="pilar.update",
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="UPDATE",
            data={"nome": "Eficácia - Updated", "ativo": False}
        )
        
        assert event_id is not None
        
        # Verify in stream
        stream_name = "intellicare:donabedian:pilar.update"
        events = redis_client.xrange(stream_name, count=1)
        
        msg_id, msg_data = events[0]
        assert msg_data["operation"] == "UPDATE"

    def test_publish_pilar_delete_event(
        self,
        publisher: EventPublisher,
        redis_client: redis.Redis
    ):
        """Test publishing a pilar.delete event."""
        pilar_id = uuid4()
        
        # Publish delete event
        event_id = publisher.publish_sync(
            event_type="pilar.delete",
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="DELETE",
            data={"reason": "Pilar inativo"}
        )
        
        assert event_id is not None
        
        # Verify in stream
        stream_name = "intellicare:donabedian:pilar.delete"
        events = redis_client.xrange(stream_name, count=1)
        
        msg_id, msg_data = events[0]
        assert msg_data["operation"] == "DELETE"

    def test_event_callback_function(
        self,
        publisher: EventPublisher,
        redis_client: redis.Redis
    ):
        """Test the callback function for OperationalDataAccess."""
        callback = get_event_callback(publisher)
        
        pilar_id = uuid4()
        
        # Call callback directly (as would happen from OperationalDataAccess)
        callback(
            operation="CREATE",
            entity_type="Pilar",
            entity_id=pilar_id,
            details={"nome": "Test", "tipo": "ESTRUTURA"}
        )
        
        # Verify event was published
        stream_name = "intellicare:donabedian:pilar.create"
        events = redis_client.xrange(stream_name, count=1)
        
        assert len(events) >= 1
        msg_id, msg_data = events[0]
        assert msg_data["entity_id"] == str(pilar_id)

    def test_multiple_events_in_sequence(
        self,
        publisher: EventPublisher,
        redis_client: redis.Redis
    ):
        """Test publishing multiple events in sequence."""
        pilar_id = uuid4()
        
        # CREATE
        publisher.publish_sync(
            event_type="pilar.create",
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="CREATE",
            data={"nome": "Eficácia"}
        )
        
        # UPDATE
        publisher.publish_sync(
            event_type="pilar.update",
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="UPDATE",
            data={"nome": "Eficácia Updated"}
        )
        
        # DELETE
        publisher.publish_sync(
            event_type="pilar.delete",
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="DELETE",
            data={"reason": "Test"}
        )
        
        # Verify events exist in their respective streams
        create_events = redis_client.xrange("intellicare:donabedian:pilar.create", count=1)
        update_events = redis_client.xrange("intellicare:donabedian:pilar.update", count=1)
        delete_events = redis_client.xrange("intellicare:donabedian:pilar.delete", count=1)
        
        assert len(create_events) >= 1
        assert len(update_events) >= 1
        assert len(delete_events) >= 1

    def test_event_has_timestamp(
        self,
        publisher: EventPublisher,
        redis_client: redis.Redis
    ):
        """Test that events include ISO timestamp."""
        pilar_id = uuid4()
        before = datetime.utcnow()
        
        publisher.publish_sync(
            event_type="pilar.create",
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="CREATE",
            data={}
        )
        
        after = datetime.utcnow()
        
        stream_name = "intellicare:donabedian:pilar.create"
        events = redis_client.xrange(stream_name, count=1)
        msg_id, msg_data = events[0]
        
        # Verify timestamp is present
        assert "timestamp" in msg_data
        
        # Verify timestamp is ISO format
        ts = datetime.fromisoformat(msg_data["timestamp"])
        assert before <= ts <= after


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not installed")
class TestEventPublisherWithoutRedis:
    """Test publisher graceful handling when Redis is unavailable."""

    def test_publisher_initializes(self):
        """Test publisher can be initialized without immediate connection."""
        publisher = EventPublisher("redis://localhost:6379")
        assert publisher.redis_url == "redis://localhost:6379"

    def test_publisher_handles_connection_error(self):
        """Test publisher handles connection errors gracefully."""
        # Use invalid Redis URL
        publisher = EventPublisher("redis://invalid:9999")
        
        # Should raise error on actual connection attempt
        with pytest.raises(Exception):
            publisher._get_redis_sync()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
