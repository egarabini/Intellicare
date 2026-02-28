"""
Consolidation worker for donabedian module.

Runs the ConsolidationConsumer that:
1. Listens to Redis events (pilar.create, pilar.update, pilar.delete)
2. Consolidates data from operacional to analitico schema
3. Updates consolidated_at timestamp
4. ACKs events in Redis Streams

Can be run as:
- Command line: python -m donabedian.consolidation.worker
- Or imported and used in FastAPI lifespan
"""

import asyncio
import logging
import os
import signal
from typing import Optional, Any

logger = logging.getLogger(__name__)


class DonabedianConsolidationConsumer:
    """
    Redis Streams consumer for donabedian consolidation.
    
    Extends intellicare_core ConsolidationConsumer with donabedian-specific logic.
    """

    def __init__(
        self,
        redis_url: str,
        db_url: str,
        consumer_id: str = "donabedian-consolidation-worker-1",
        batch_size: int = 100,
    ):
        """
        Initialize consumer.
        
        Args:
            redis_url: Redis connection URL
            db_url: PostgreSQL connection URL
            consumer_id: Unique consumer ID
            batch_size: Events per batch
        """
        self.redis_url = redis_url
        self.db_url = db_url
        self.consumer_id = consumer_id
        self.batch_size = batch_size
        
        self._redis: Optional[Any] = None
        self._running = False
        self._consolidation_service: Optional[Any] = None

    async def _get_redis(self):
        """Get or initialize Redis connection."""
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = await aioredis.from_url(self.redis_url)
        return self._redis

    async def _get_consolidation_service(self):
        """Get or initialize consolidation service."""
        if self._consolidation_service is None:
            from donabedian.consolidation.service import DonabedianConsolidationService
            self._consolidation_service = DonabedianConsolidationService(self.db_url)
        return self._consolidation_service

    async def setup_consumer_groups(self):
        """Create consumer groups for each stream."""
        redis = await self._get_redis()

        streams = [
            "intellicare:donabedian:pilar.create",
            "intellicare:donabedian:pilar.update",
            "intellicare:donabedian:pilar.delete",
            "intellicare:donabedian:indicator.create",
            "intellicare:donabedian:indicator.update",
            "intellicare:donabedian:indicator.delete",
            "intellicare:donabedian:measurement.create",
            "intellicare:donabedian:measurement.update",
            "intellicare:donabedian:measurement.delete",
        ]

        for stream_name in streams:
            group_name = "donabedian-consolidation"

            try:
                # Create consumer group (idempotent)
                await redis.xgroup_create(
                    stream_name,
                    group_name,
                    id="0",
                    mkstream=True
                )
                logger.info(f"✅ Consumer group '{group_name}' created for {stream_name}")
            except Exception as e:
                if "BUSYGROUP" in str(e):
                    logger.debug(f"Consumer group '{group_name}' already exists for {stream_name}")
                else:
                    logger.warning(f"Error creating consumer group for {stream_name}: {e}")

    async def process_pilar_event(
        self,
        stream_name: str,
        message: dict
    ) -> bool:
        """Process a Pilar event."""
        try:
            # Parse message
            entity_id = message.get("entity_id")
            operation = message.get("operation")
            data_raw = message.get("data")
            timestamp = message.get("timestamp")

            if not all([entity_id, operation, timestamp]):
                logger.warning(f"Incomplete message: {message}")
                return False

            # Parse data JSON
            import json
            data = json.loads(data_raw) if isinstance(data_raw, str) else data_raw

            # Route to consolidation service
            consolidation = await self._get_consolidation_service()
            success = await consolidation.consolidate(
                entity_type="Pilar",
                entity_id=entity_id,
                operation=operation,
                old_values=data.get("old_values"),
                new_values=data.get("new_values"),
                timestamp=timestamp
            )

            return success

        except Exception as e:
            logger.error(f"Error processing pilar event: {e}", exc_info=True)
            return False

    async def process_indicator_event(
        self,
        stream_name: str,
        message: dict
    ) -> bool:
        """Process an Indicator event."""
        try:
            # Parse message
            entity_id = message.get("entity_id")
            operation = message.get("operation")
            data_raw = message.get("data")
            timestamp = message.get("timestamp")

            if not all([entity_id, operation, timestamp]):
                logger.warning(f"Incomplete message: {message}")
                return False

            # Parse data JSON
            import json
            data = json.loads(data_raw) if isinstance(data_raw, str) else data_raw

            # Route to consolidation service
            consolidation = await self._get_consolidation_service()
            success = await consolidation.consolidate(
                entity_type="Indicator",
                entity_id=entity_id,
                operation=operation,
                old_values=data.get("old_values"),
                new_values=data.get("new_values"),
                timestamp=timestamp
            )

            return success

        except Exception as e:
            logger.error(f"Error processing indicator event: {e}", exc_info=True)
            return False

    async def process_measurement_event(
        self,
        stream_name: str,
        message: dict
    ) -> bool:
        """Process a Measurement event."""
        try:
            # Parse message
            entity_id = message.get("entity_id")
            operation = message.get("operation")
            data_raw = message.get("data")
            timestamp = message.get("timestamp")

            if not all([entity_id, operation, timestamp]):
                logger.warning(f"Incomplete message: {message}")
                return False

            # Parse data JSON
            import json
            data = json.loads(data_raw) if isinstance(data_raw, str) else data_raw

            # Route to consolidation service
            consolidation = await self._get_consolidation_service()
            success = await consolidation.consolidate(
                entity_type="Measurement",
                entity_id=entity_id,
                operation=operation,
                old_values=data.get("old_values"),
                new_values=data.get("new_values"),
                timestamp=timestamp
            )

            return success

        except Exception as e:
            logger.error(f"Error processing measurement event: {e}", exc_info=True)
            return False

    async def process_event(
        self,
        stream_name: str,
        message: dict
    ) -> bool:
        """Process an event based on stream type."""
        try:
            # Route to appropriate handler based on stream name
            if "pilar" in stream_name:
                return await self.process_pilar_event(stream_name, message)
            elif "indicator" in stream_name:
                return await self.process_indicator_event(stream_name, message)
            elif "measurement" in stream_name:
                return await self.process_measurement_event(stream_name, message)
            else:
                logger.warning(f"Unknown stream type: {stream_name}")
                return False

        except Exception as e:
            logger.error(f"Error processing event from {stream_name}: {e}")
            return False

    async def consume_events(self):
        """Main consumer loop."""
        redis = await self._get_redis()
        await self.setup_consumer_groups()

        self._running = True
        group_name = "donabedian-consolidation"

        logger.info("🚀 Starting consolidation consumer...")

        while self._running:
            try:
                # Read from all streams
                streams = {
                    "intellicare:donabedian:pilar.create": ">",
                    "intellicare:donabedian:pilar.update": ">",
                    "intellicare:donabedian:pilar.delete": ">",
                    "intellicare:donabedian:indicator.create": ">",
                    "intellicare:donabedian:indicator.update": ">",
                    "intellicare:donabedian:indicator.delete": ">",
                    "intellicare:donabedian:measurement.create": ">",
                    "intellicare:donabedian:measurement.update": ">",
                    "intellicare:donabedian:measurement.delete": ">",
                }

                messages = await redis.xreadgroup(
                    streams,
                    group_name,
                    self.consumer_id,
                    count=self.batch_size,
                    block=5000,  # 5 second timeout
                )

                if not messages:
                    # logger.debug("No new events")
                    continue

                # Process batch
                for stream_key, stream_messages in messages:
                    stream_name = stream_key if isinstance(stream_key, str) else stream_key.decode()

                    for stream_id, message in stream_messages:
                        msg_id = stream_id if isinstance(stream_id, str) else stream_id.decode()

                        # Decode message values
                        decoded_message = {}
                        for k, v in message.items():
                            key = k if isinstance(k, str) else k.decode()
                            val = v if isinstance(v, str) else v.decode()
                            decoded_message[key] = val

                        logger.info(f"📝 Processing event: {msg_id} from {stream_name}")

                        # Process
                        success = await self.process_event(stream_name, decoded_message)

                        # ACK if successful
                        if success:
                            await redis.xack(stream_name, group_name, msg_id)
                            logger.info(f"✅ ACK: {msg_id}")
                        else:
                            logger.warning(f"❌ NACK (will retry): {msg_id}")

            except asyncio.CancelledError:
                logger.info("Consumer cancelled")
                break
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Backoff

        logger.info("Consumer loop stopped")

    async def start(self):
        """Start the consumer."""
        try:
            await self.consume_events()
        finally:
            await self.close()

    async def stop(self):
        """Stop the consumer gracefully."""
        logger.info("Stopping consolidation consumer...")
        self._running = False

    async def close(self):
        """Close all connections."""
        logger.info("Closing consolidation consumer...")
        self._running = False

        if self._consolidation_service:
            await self._consolidation_service.close()

        if self._redis:
            await self._redis.close()
            self._redis = None

        logger.info("✅ Consolidation consumer closed")


async def run_consumer():
    """Run the consolidation consumer."""
    # Get config from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin_intellicare:Crazy%23-57@161.97.141.186:5432/IntellicareDB")

    logger.info(f"Redis URL: {redis_url}")
    logger.info(f"Database URL: {db_url[:50]}...")

    consumer = DonabedianConsolidationConsumer(
        redis_url=redis_url,
        db_url=db_url,
    )

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, stopping consumer...")
        asyncio.create_task(consumer.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start consumer
    await consumer.start()


def main():
    """Entry point for CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(run_consumer())


if __name__ == "__main__":
    main()
