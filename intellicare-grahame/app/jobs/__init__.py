"""
Jobs package for intellicare-grahame.

Provides BullMQ worker management with Redis failover handling.
"""

from app.jobs.failover import (
    BullMQWorkerWithFailover,
    FailoverConfig,
    RedisFailoverHandler,
)

__all__ = [
    "RedisFailoverHandler",
    "BullMQWorkerWithFailover",
    "FailoverConfig",
]
