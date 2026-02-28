"""
Redis Failover Handler for BullMQ Workers.

Implements automatic reconnection with exponential backoff,
job requeuing on failover, and Dead Letter Queue (DLQ) for failed jobs.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    import aioredis  # type: ignore


def _redis_exception_types() -> tuple[type[BaseException], ...]:
    """Build a safe tuple of redis exception types, resilient to mocked modules."""
    candidates: list[type[BaseException]] = []
    for name in ("ConnectionError", "TimeoutError"):
        exc = getattr(aioredis, name, None)
        if isinstance(exc, type) and issubclass(exc, BaseException):
            candidates.append(exc)
    if candidates:
        return tuple(candidates)
    return (ConnectionError, TimeoutError)


REDIS_EXCEPTIONS = _redis_exception_types()

logger = logging.getLogger(__name__)


@dataclass
class FailoverConfig:
    """Configuration for Redis failover handler."""

    # Retry configuration
    initial_delay_seconds: int = 1
    exponential_base: float = 2.0
    max_delay_seconds: int = 30
    max_retries: int = 10  # -1 = infinite retries

    # Job recovery
    requeue_jobs_on_reconnect: bool = True
    dlq_threshold: int = 3  # Move to DLQ after N failures


class RedisFailoverHandler:
    """
    Handle Redis connection failures with automatic reconnection.

    Features:
    - Exponential backoff reconnection (1s → 2s → 4s → ... → 30s max)
    - Job requeuing on reconnect (recover in-flight jobs)
    - Dead Letter Queue (DLQ) for repeatedly failed jobs
    - Metrics tracking (failover count, retry count, DLQ size)
    """

    def __init__(
        self,
        redis_url: str,
        config: Optional[FailoverConfig] = None,
    ):
        """
        Initialize failover handler.

        Args:
            redis_url: Redis URL (redis://localhost:6379/0)
            config: Failover configuration (uses defaults if None)
        """
        self._redis_url = redis_url
        self._config = config or FailoverConfig()
        self._redis: Optional[aioredis.Redis] = None
        self._is_connected = False
        self._failover_count = 0
        self._retry_count = 0

    async def connect(self) -> aioredis.Redis:
        """
        Connect to Redis with automatic retry on failure.

        Returns:
            Connected Redis client

        Raises:
            ConnectionError: If max retries exceeded
        """
        delay = self._config.initial_delay_seconds

        for attempt in range(self._config.max_retries):
            try:
                logger.info(f"Connecting to Redis (attempt {attempt + 1})...")

                self._redis = await aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )

                # Verify connection
                await self._redis.ping()
                self._is_connected = True

                logger.info("Connected to Redis successfully")
                return self._redis

            except REDIS_EXCEPTIONS as e:
                self._retry_count += 1
                logger.warning(
                    f"Redis connection failed (attempt {attempt + 1}): {e}. "
                    f"Retrying in {delay} seconds..."
                )

                # Exponential backoff
                await asyncio.sleep(delay)
                delay = min(
                    delay * self._config.exponential_base,
                    self._config.max_delay_seconds,
                )

        # Max retries exceeded
        error_msg = f"Failed to connect to Redis after {self._config.max_retries} attempts"
        logger.error(error_msg)
        raise ConnectionError(error_msg)

    async def disconnect(self) -> None:
        """Disconnect from Redis gracefully."""
        if self._redis:
            await self._redis.close()
            self._is_connected = False
            logger.info("Disconnected from Redis")

    async def _handle_connection_loss(self) -> None:
        """
        Handle connection loss (called when Redis becomes unavailable).

        This method is called when a Redis operation fails due to
        connection loss. It triggers reconnection with backoff.
        """
        self._failover_count += 1
        self._is_connected = False

        logger.error(f"Redis connection lost (failover #{self._failover_count})")

        try:
            # Attempt to reconnect
            await self.connect()

            # Reconnection successful
            logger.info("Redis reconnection successful")

            # TODO: Re-enqueue in-flight jobs
            if self._config.requeue_jobs_on_reconnect:
                await self._requeue_in_flight_jobs()

        except ConnectionError as e:
            # Reconnection failed
            logger.error(f"Redis reconnection failed: {e}")
            raise

    async def _requeue_in_flight_jobs(self) -> None:
        """
        Re-enqueue jobs that were in-flight during failover.

        Strategy:
        1. Scan BullMQ queues for jobs in 'active' state
        2. Move them back to 'waiting' state
        3. Jobs will be picked up by workers again

        Note: This is a simplified implementation. A production system
        would need more sophisticated tracking of in-flight jobs.
        """
        logger.info("Re-enqueuing in-flight jobs...")

        # Get all BullMQ queues
        queues = await self._redis.keys("bull:*")

        requeued_count = 0

        for queue_key in queues:
            # Get active jobs for this queue
            active_key = f"{queue_key}:active"
            active_jobs = await self._redis.lrange(active_key, 0, -1)

            for job_id in active_jobs:
                # Move from active to waiting
                waiting_key = f"{queue_key}:waiting"
                await self._redis.rpush(waiting_key, job_id)
                await self._redis.lrem(active_key, 1, job_id)
                requeued_count += 1

        logger.info(f"Re-enqueued {requeued_count} jobs")

    async def execute_with_retry(
        self,
        operation: callable,
        *args,
        **kwargs,
    ):
        """
        Execute Redis operation with automatic retry on connection failure.

        Args:
            operation: Redis operation (e.g., redis.set)
            *args: Arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation

        Returns:
            Result of operation

        Raises:
            ConnectionError: If retry fails
        """
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                # Ensure connected
                if not self._is_connected or self._redis is None:
                    await self.connect()

                # Execute operation
                return await operation(self._redis, *args, **kwargs)

            except REDIS_EXCEPTIONS as e:
                logger.warning(
                    f"Redis operation failed (attempt {attempt + 1}): {e}"
                )

                # Handle connection loss
                if attempt < max_attempts - 1:
                    await self._handle_connection_loss()
                else:
                    raise

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._is_connected

    @property
    def failover_count(self) -> int:
        """Get number of failovers that occurred."""
        return self._failover_count

    @property
    def retry_count(self) -> int:
        """Get number of retry attempts."""
        return self._retry_count


class BullMQWorkerWithFailover:
    """
    BullMQ worker with automatic Redis failover handling.

    Wraps a BullMQ worker and adds failover capabilities:
    - Automatic reconnection on connection loss
    - Job requeuing after failover
    - DLQ for repeatedly failed jobs
    """

    def __init__(
        self,
        queue_name: str,
        processor: callable,
        redis_url: str,
        failover_config: Optional[FailoverConfig] = None,
    ):
        """
        Initialize worker with failover.

        Args:
            queue_name: BullMQ queue name
            processor: Job processor function
            redis_url: Redis URL
            failover_config: Failover configuration
        """
        self._queue_name = queue_name
        self._processor = processor
        self._failover_handler = RedisFailoverHandler(redis_url, failover_config)
        self._worker = None

    async def start(self) -> None:
        """Start worker with failover handling."""
        # Connect to Redis
        await self._failover_handler.connect()

        # Create BullMQ worker
        # Note: This is a placeholder. Actual BullMQ Python implementation
        # would use the 'bullmq' package or similar.
        # For now, we'll simulate the worker pattern.
        logger.info(f"Starting worker for queue: {self._queue_name}")

        # TODO: Create actual BullMQ worker
        # self._worker = Worker(self._queue_name, self._processor, { connection: redis })

    async def stop(self) -> None:
        """Stop worker gracefully."""
        if self._worker:
            await self._worker.close()
        await self._failover_handler.disconnect()

    async def _process_job_with_retry(self, job: dict) -> None:
        """
        Process job with automatic retry on failure.

        Moves job to DLQ after exceeding failure threshold.

        Args:
            job: BullMQ job data
        """
        failure_count = job.get("attemptsMade", 0)

        try:
            # Process job
            await self._processor(job)

        except Exception as e:
            logger.error(f"Job {job.get('id')} failed: {e}")

            # Increment failure count
            failure_count += 1

            # Check if should move to DLQ
            if failure_count >= self._failover_handler._config.dlq_threshold:
                # Move to Dead Letter Queue
                await self._move_to_dlq(job, str(e))
            else:
                # Retry job
                # TODO: Implement BullMQ job retry
                pass

    async def _move_to_dlq(self, job: dict, error: str) -> None:
        """
        Move failed job to Dead Letter Queue.

        Args:
            job: Failed job
            error: Error message
        """
        dlq_key = f"{self._queue_name}:dlq"

        # Add to DLQ
        await self._failover_handler.execute_with_retry(
            lambda redis_client, key, payload: redis_client.rpush(key, payload),
            dlq_key,
            str({**job, "error": error, "failedAt": datetime.now().isoformat()}),
        )

        logger.warning(f"Job {job.get('id')} moved to DLQ after {job.get('attemptsMade', 0)} failures")
