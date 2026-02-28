"""
Jobs health check routes.

Provides health check endpoints for BullMQ workers and Redis connections.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from grahame.api.deps import get_redis
from app.jobs.failover import RedisFailoverHandler

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobsHealthResponse(BaseModel):
    """Health check response for jobs."""

    status: str
    redis: dict
    jobs: dict
    workers: dict


@router.get("/health", response_model=JobsHealthResponse)
async def jobs_health(
    redis=Depends(get_redis),
) -> JobsHealthResponse:
    """
    Health check for BullMQ workers and Redis.

    Returns:
        Health status including Redis connection, job counts, and worker status
    """
    # Check Redis connection
    redis_connected = False
    redis_mode = "unknown"

    try:
        if redis:
            await redis.ping()
            redis_connected = True

            # Check Redis mode (standalone, sentinel, cluster)
            info = await redis.info("replication")
            redis_mode = "sentinel" if info.get("role") == "sentinel" else "standalone"

    except Exception as e:
        redis_connected = False
        redis_mode = f"error: {str(e)}"

    # Get job counts (placeholder - would query BullMQ queues)
    # TODO: Implement actual BullMQ queue stats
    jobs_stats = {
        "waiting": 0,
        "active": 0,
        "completed": 0,
        "failed": 0,
        "delayed": 0,
    }

    # Worker status (placeholder)
    workers_stats = {
        "active": 0,
        "paused": False,
    }

    # Determine overall status
    status = "healthy" if redis_connected else "unhealthy"

    return JobsHealthResponse(
        status=status,
        redis={
            "connected": redis_connected,
            "mode": redis_mode,
        },
        jobs=jobs_stats,
        workers=workers_stats,
    )
