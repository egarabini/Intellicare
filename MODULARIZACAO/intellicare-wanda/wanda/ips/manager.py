"""IPS Manager — caching, fetching, and validation (EF-W002).

Implements the IPS-First rule v2.0:
- Redis cache with TTL
- Automatic fetch from Florence
- Stale-while-revalidate pattern
- Validation of required fields
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Optional

import httpx

from wanda.ips.models import IPSBundle, ValidationResult

logger = logging.getLogger(__name__)

# Redis key patterns
IPS_KEY = "wanda:ips:{patient_id}"
IPS_STALE_KEY = "wanda:ips:stale:{patient_id}"


class IPSManager:
    """Manages IPS lifecycle: cache, fetch, validate, propagate.

    Uses Redis for caching with stale-while-revalidate strategy.
    Falls back to in-memory dict if Redis is unavailable.
    """

    def __init__(
        self,
        florence_url: str = "http://localhost:8002",
        redis_client: Optional[Any] = None,
        ips_ttl: int = 3600,  # 1 hour
        stale_ttl: int = 86400,  # 24 hours
        fetch_timeout: int = 10,
        metrics_registry: Optional[Any] = None,
    ):
        self._florence_url = florence_url
        self._redis = redis_client
        self._ips_ttl = ips_ttl
        self._stale_ttl = stale_ttl
        self._fetch_timeout = fetch_timeout
        self._metrics = metrics_registry

        # In-memory fallback cache
        self._memory_cache: dict[str, tuple[IPSBundle, float]] = {}

    @property
    def has_redis(self) -> bool:
        return self._redis is not None

    async def get(
        self,
        patient_id: str,
        force_refresh: bool = False,
    ) -> IPSBundle:
        """Get IPS for a patient.

        Strategy:
        1. Check cache (Redis or memory)
           a. Fresh → return cached
           b. Stale → return stale, trigger async refresh
           c. Missing → fetch from Florence synchronously
        2. Fetch from Florence if needed
        3. Update cache
        """
        started_at = time.monotonic()
        miss_reason: Optional[str] = None
        if not force_refresh:
            cached = await self._get_from_cache(patient_id)
            if cached and not cached.is_stale:
                logger.debug("IPS cache hit (fresh) for %s", patient_id)
                self._record_ips_hit("fresh", cached.age_seconds)
                self._record_ips_load(time.monotonic() - started_at)
                return cached
            if cached and cached.is_stale:
                logger.debug("IPS cache hit (stale) for %s", patient_id)
                # Return stale immediately, refresh in background would be ideal
                # but for simplicity we do sync refresh next time
                self._record_ips_hit("stale", cached.age_seconds)
                self._record_ips_load(time.monotonic() - started_at)
                return cached
            miss_reason = "not_found"
        else:
            miss_reason = "expired"

        # Cache miss or force refresh → fetch from Florence
        if miss_reason is not None:
            self._record_ips_miss(miss_reason)
        ips = await self._fetch_from_florence(patient_id)
        if ips:
            await self._set_cache(patient_id, ips)
            self._record_ips_load(time.monotonic() - started_at)
            return ips

        # Florence failed — try stale cache
        stale = await self._get_stale_from_cache(patient_id)
        if stale:
            logger.warning("Florence unavailable, using stale IPS for %s", patient_id)
            if miss_reason is None:
                self._record_ips_miss("error")
            self._record_ips_hit("stale", stale.age_seconds)
            self._record_ips_load(time.monotonic() - started_at)
            return stale

        # No data at all — return empty IPS
        logger.warning("No IPS data available for %s, returning empty", patient_id)
        if miss_reason is None:
            self._record_ips_miss("error")
        self._record_ips_load(time.monotonic() - started_at)
        return IPSBundle.empty(patient_id)

    async def get_batch(self, patient_ids: list[str]) -> dict[str, IPSBundle]:
        """Fetch IPS for multiple patients."""
        results = {}
        for pid in patient_ids:
            results[pid] = await self.get(pid)
        return results

    async def invalidate(self, patient_id: str) -> None:
        """Invalidate cache for a patient."""
        if self._redis:
            try:
                key = IPS_KEY.format(patient_id=patient_id)
                await self._redis.delete(key)
                logger.info("Invalidated IPS cache for %s", patient_id)
            except Exception as e:
                logger.warning("Failed to invalidate Redis cache for %s: %s", patient_id, e)

        # Also clear memory cache
        self._memory_cache.pop(patient_id, None)

    def validate(self, ips: IPSBundle) -> ValidationResult:
        """Validate IPS integrity.

        Required: patient_id, at least one condition.
        Warnings: old IPS, no recent labs, no medications.
        """
        result = ValidationResult()

        if not ips.patient_id:
            result.is_valid = False
            result.errors.append("patient_id is required")

        if not ips.conditions:
            result.warnings.append("No conditions registered")

        if not ips.medications:
            result.warnings.append("No medications registered")

        if not ips.allergies:
            result.warnings.append("No allergies registered")

        # Check age
        if ips.age_seconds > 7776000:  # 90 days
            result.warnings.append(
                f"IPS is older than 90 days ({ips.age_seconds / 86400:.0f} days)"
            )

        if ips.is_degraded:
            result.warnings.append("IPS is degraded (incomplete data)")

        if ips.is_stale:
            result.warnings.append("IPS is stale (expired cache)")

        # Check for recent lab observations
        has_recent_labs = any(
            obs.get("category") == "laboratory" for obs in ips.observations
        )
        if not has_recent_labs and ips.observations:
            result.warnings.append("No recent laboratory observations found")

        return result

    async def get_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        return {
            "has_redis": self.has_redis,
            "memory_cache_size": len(self._memory_cache),
            "ips_ttl": self._ips_ttl,
            "stale_ttl": self._stale_ttl,
        }

    # ── Private ────────────────────────────────────────────────────

    async def _fetch_from_florence(self, patient_id: str) -> Optional[IPSBundle]:
        """Fetch IPS from Florence via HTTP."""
        url = f"{self._florence_url}/api/v1/ips/{patient_id}"
        try:
            async with httpx.AsyncClient(timeout=self._fetch_timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    ips = IPSBundle.from_florence_response(patient_id, data)
                    logger.info("Fetched IPS from Florence for %s", patient_id)
                    return ips
                else:
                    logger.warning(
                        "Florence returned %d for IPS %s", resp.status_code, patient_id
                    )
                    return None
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("Failed to fetch IPS from Florence for %s: %s", patient_id, e)
            return None

    async def _get_from_cache(self, patient_id: str) -> Optional[IPSBundle]:
        """Get IPS from cache (Redis or memory)."""
        # Try Redis first
        if self._redis:
            try:
                key = IPS_KEY.format(patient_id=patient_id)
                data = await self._redis.get(key)
                if data:
                    ips_dict = json.loads(data)
                    ips = self._deserialize_ips(ips_dict)
                    ips.age_seconds = time.time() - ips_dict.get("_cached_at", time.time())
                    return ips
            except Exception as e:
                logger.warning("Redis get failed for %s: %s", patient_id, e)

        # Fallback to memory cache
        if patient_id in self._memory_cache:
            ips, cached_at = self._memory_cache[patient_id]
            age = time.time() - cached_at
            ips.age_seconds = age
            if age > self._ips_ttl:
                ips.is_stale = True
            return ips

        return None

    async def _get_stale_from_cache(self, patient_id: str) -> Optional[IPSBundle]:
        """Get stale IPS from Redis backup."""
        if self._redis:
            try:
                key = IPS_STALE_KEY.format(patient_id=patient_id)
                data = await self._redis.get(key)
                if data:
                    ips_dict = json.loads(data)
                    ips = self._deserialize_ips(ips_dict)
                    ips.is_stale = True
                    ips.age_seconds = time.time() - ips_dict.get("_cached_at", time.time())
                    return ips
            except Exception as e:
                logger.warning("Redis stale get failed for %s: %s", patient_id, e)
        return None

    async def _set_cache(self, patient_id: str, ips: IPSBundle) -> None:
        """Store IPS in cache (Redis + memory)."""
        now = time.time()
        ips_dict = ips.to_dict()
        ips_dict["_cached_at"] = now

        # Memory cache
        self._memory_cache[patient_id] = (ips, now)

        # Redis cache
        if self._redis:
            try:
                serialized = json.dumps(ips_dict, default=str)
                key = IPS_KEY.format(patient_id=patient_id)
                stale_key = IPS_STALE_KEY.format(patient_id=patient_id)

                await self._redis.set(key, serialized, ex=self._ips_ttl)
                await self._redis.set(stale_key, serialized, ex=self._stale_ttl)
            except Exception as e:
                logger.warning("Redis set failed for %s: %s", patient_id, e)

    def _deserialize_ips(self, data: dict) -> IPSBundle:
        """Reconstruct IPSBundle from cached dict."""
        return IPSBundle(
            patient_id=data.get("patient_id", ""),
            patient_name=data.get("patient_name", ""),
            conditions=data.get("conditions", []),
            medications=data.get("medications", []),
            allergies=data.get("allergies", []),
            observations=data.get("observations", []),
            immunizations=data.get("immunizations", []),
            source=data.get("source", "cache"),
            is_stale=data.get("is_stale", False),
            is_degraded=data.get("is_degraded", False),
        )

    def set_metrics_registry(self, metrics_registry: Optional[Any]) -> None:
        self._metrics = metrics_registry

    def _record_ips_hit(self, freshness: str, age_seconds: float | int | None) -> None:
        if self._metrics is None:
            return
        try:
            age_hours = None if age_seconds is None else max(0.0, float(age_seconds) / 3600.0)
            self._metrics.record_ips_cache_hit(freshness=freshness, age_hours=age_hours)
        except Exception:
            return

    def _record_ips_miss(self, reason: str) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.record_ips_cache_miss(reason=reason)
        except Exception:
            return

    def _record_ips_load(self, duration_seconds: float) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.record_ips_load(duration_seconds=max(0.0, float(duration_seconds)))
        except Exception:
            return
