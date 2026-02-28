"""Discovery Service — probes modules via HTTP and persists results (EF-W001).

Evolutionary replacement for the v1.0 ModuleRegistry.discover() method.
Adds periodic health checks, persistent history, and routing table derivation.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

import httpx

from wanda.discovery.models import ModuleInfo, ModuleStatus
from wanda.registry.persistent_registry import PersistentModuleRegistry

logger = logging.getLogger(__name__)


class DiscoveryResult:
    """Result of a discovery sweep."""

    def __init__(self):
        self.discovered: list[str] = []
        self.failed: list[str] = []
        self.total_time_ms: float = 0.0

    @property
    def success_count(self) -> int:
        return len(self.discovered)

    @property
    def failure_count(self) -> int:
        return len(self.failed)

    def to_dict(self) -> dict:
        return {
            "discovered": self.discovered,
            "failed": self.failed,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_time_ms": round(self.total_time_ms, 1),
        }


class DiscoveryService:
    """Discovers modules via HTTP and persists into PersistentModuleRegistry.

    Probes /api/v1/health and /api/v1/info on each known host.
    Results are stored both in-memory (for fast routing) and in PostgreSQL
    (for history/audit).
    """

    def __init__(
        self,
        registry: PersistentModuleRegistry,
        known_hosts: dict[str, str],
        timeout_seconds: int = 5,
        health_check_interval: int = 30,
    ):
        self._registry = registry
        self._known_hosts = known_hosts
        self._timeout = timeout_seconds
        self._health_check_interval = health_check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def discover_all(self) -> DiscoveryResult:
        """Probe all known hosts. Returns DiscoveryResult."""
        result = DiscoveryResult()
        start = time.monotonic()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            tasks = [
                self._probe_and_register(client, name, url)
                for name, url in self._known_hosts.items()
            ]
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)

            for name, outcome in zip(self._known_hosts.keys(), outcomes):
                if isinstance(outcome, Exception):
                    result.failed.append(name)
                    logger.warning("Discovery exception for %s: %s", name, outcome)
                elif outcome is True:
                    result.discovered.append(name)
                else:
                    result.failed.append(name)

        result.total_time_ms = (time.monotonic() - start) * 1000
        self._registry._last_discovery = datetime.now()

        logger.info(
            "Discovery complete: %d ok, %d failed (%.0f ms)",
            result.success_count,
            result.failure_count,
            result.total_time_ms,
        )
        return result

    async def discover_single(self, agent_name: str) -> Optional[ModuleInfo]:
        """Re-discover a single agent."""
        url = self._known_hosts.get(agent_name)
        if not url:
            return None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            success = await self._probe_and_register(client, agent_name, url)

        if success:
            return self._registry.get_module(agent_name)
        return None

    async def _probe_and_register(
        self,
        client: httpx.AsyncClient,
        name: str,
        base_url: str,
    ) -> bool:
        """Probe a single module and register/update result."""
        module = ModuleInfo(name=name, base_url=base_url)

        # Step 1: GET /api/v1/info
        try:
            resp = await client.get(f"{base_url}/api/v1/info")
            if resp.status_code == 200:
                data = resp.json()
                module.version = data.get("version", "")
                module.description = data.get("description", "")
                module.capabilities = data.get("capabilities", [])
                module.status = ModuleStatus.ONLINE
                module.last_check = datetime.now()
            else:
                module.status = ModuleStatus.OFFLINE
        except (httpx.RequestError, httpx.TimeoutException):
            module.status = ModuleStatus.OFFLINE

        # Step 2: GET /api/v1/health (if info succeeded)
        if module.status == ModuleStatus.ONLINE:
            try:
                resp = await client.get(f"{base_url}/api/v1/health")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") != "healthy":
                        module.status = ModuleStatus.DEGRADED
                else:
                    module.status = ModuleStatus.DEGRADED
            except (httpx.RequestError, httpx.TimeoutException):
                module.status = ModuleStatus.DEGRADED

        # Step 3: Persist to registry
        await self._registry.register_or_update(module)

        # Step 4: Update health status in DB
        if module.status == ModuleStatus.OFFLINE:
            await self._registry.mark_unhealthy(name, "Discovery probe failed")
            return False
        elif module.status == ModuleStatus.DEGRADED:
            # Still usable but degraded
            return True
        else:
            await self._registry.mark_healthy(name)
            return True

    async def get_routing_table(self) -> dict:
        """Derive routing table from current registry state."""
        return await self._registry.get_routing_table()

    # ── Periodic Health Check ──────────────────────────────────────

    async def start_periodic_checks(self) -> None:
        """Start background periodic health checks."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info(
            "Periodic health checks started (interval=%ds)", self._health_check_interval
        )

    async def stop_periodic_checks(self) -> None:
        """Stop background periodic health checks."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Periodic health checks stopped")

    async def _health_check_loop(self) -> None:
        """Background loop for periodic discovery."""
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval)
                if self._running:
                    await self.discover_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check loop error: %s", e)
                await asyncio.sleep(5)
