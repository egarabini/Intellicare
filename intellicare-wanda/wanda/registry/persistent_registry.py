"""Persistent Module Registry v2 — PostgreSQL-backed (EF-W001).

Maintains backward compatibility with v1.0 in-memory interface
while persisting all data to PostgreSQL.
"""

import logging
from datetime import datetime
from typing import Optional

from wanda.database.repository import ModuleRepository
from wanda.discovery.models import ModuleInfo, ModuleStatus

logger = logging.getLogger(__name__)


class PersistentModuleRegistry:
    """Module registry backed by PostgreSQL.

    Provides the same public API as the v1.0 ModuleRegistry (in-memory),
    but persists all module data to the database when available.

    Graceful degradation: if db_repository is None, falls back to
    in-memory storage (identical to v1.0 behavior).
    """

    def __init__(
        self,
        module_urls: dict[str, str],
        db_repository: Optional[ModuleRepository] = None,
        timeout_seconds: int = 5,
    ):
        self._module_urls = module_urls
        self._db = db_repository
        self._timeout = timeout_seconds

        # In-memory cache (always maintained for v1.0 compat)
        self._modules: dict[str, ModuleInfo] = {}
        self._last_discovery: Optional[datetime] = None

    @property
    def has_persistence(self) -> bool:
        """Whether PostgreSQL persistence is available."""
        return self._db is not None

    # ── v1.0 Compatible Interface ──────────────────────────────────

    def get_online_modules(self) -> list[ModuleInfo]:
        """Return all modules that are online or degraded (v1.0 compat)."""
        return [
            m
            for m in self._modules.values()
            if m.status in (ModuleStatus.ONLINE, ModuleStatus.DEGRADED)
        ]

    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """Get a specific module by name (v1.0 compat)."""
        return self._modules.get(name)

    def get_modules_with_capability(self, capability: str) -> list[ModuleInfo]:
        """Find modules that have a specific capability (v1.0 compat)."""
        return [
            m
            for m in self._modules.values()
            if capability in m.capabilities and m.status != ModuleStatus.OFFLINE
        ]

    @property
    def total_modules(self) -> int:
        return len(self._modules)

    @property
    def online_count(self) -> int:
        return len(self.get_online_modules())

    @property
    def last_discovery(self) -> Optional[datetime]:
        return self._last_discovery

    @property
    def _module_urls_dict(self) -> dict[str, str]:
        return dict(self._module_urls)

    # ── v2.0 Persistent Operations ─────────────────────────────────

    async def register_or_update(self, module_info: ModuleInfo) -> None:
        """Register/update a module in both memory and DB."""
        # Always update in-memory
        self._modules[module_info.name] = module_info

        # Persist if DB available
        if self._db:
            try:
                port = 0
                url = module_info.base_url
                if ":" in url.split("//")[-1]:
                    try:
                        port = int(url.split(":")[-1].split("/")[0])
                    except (ValueError, IndexError):
                        pass

                await self._db.register_or_update(
                    {
                        "agent_name": module_info.name,
                        "module_type": "HTTP",
                        "version": module_info.version,
                        "description": module_info.description,
                        "base_url": module_info.base_url,
                        "port": port,
                        "capabilities": module_info.capabilities,
                    }
                )
            except Exception as e:
                logger.warning(
                    "Failed to persist module %s: %s (continuing in-memory)",
                    module_info.name,
                    e,
                )

    async def mark_unhealthy(self, agent_name: str, reason: str) -> None:
        """Mark module as unhealthy."""
        module = self._modules.get(agent_name)
        if module:
            module.status = ModuleStatus.OFFLINE

        if self._db:
            try:
                await self._db.mark_unhealthy(agent_name, reason)
            except Exception as e:
                logger.warning("Failed to persist unhealthy status for %s: %s", agent_name, e)

    async def mark_healthy(self, agent_name: str) -> None:
        """Restore module to healthy."""
        module = self._modules.get(agent_name)
        if module:
            module.status = ModuleStatus.ONLINE

        if self._db:
            try:
                await self._db.mark_healthy(agent_name)
            except Exception as e:
                logger.warning("Failed to persist healthy status for %s: %s", agent_name, e)

    async def get_health_history(
        self, agent_name: str, last_n_events: int = 50
    ) -> list[dict]:
        """Get health event history (requires DB)."""
        if not self._db:
            return []
        try:
            events = await self._db.get_health_history(agent_name, last_n_events)
            return [
                {
                    "agent_name": e.agent_name,
                    "event_type": e.event_type,
                    "previous_status": e.previous_status,
                    "new_status": e.new_status,
                    "reason": e.reason,
                    "response_time_ms": e.response_time_ms,
                    "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                }
                for e in events
            ]
        except Exception as e:
            logger.warning("Failed to fetch health history for %s: %s", agent_name, e)
            return []

    async def get_capabilities_history(
        self, agent_name: str, last_n: int = 20
    ) -> list[dict]:
        """Get capabilities version history (requires DB)."""
        if not self._db:
            return []
        try:
            records = await self._db.get_capabilities_history(agent_name, last_n)
            return [
                {
                    "agent_name": r.agent_name,
                    "version": r.version,
                    "capabilities": r.capabilities,
                    "changed_at": r.changed_at.isoformat() if r.changed_at else None,
                    "change_type": r.change_type,
                }
                for r in records
            ]
        except Exception as e:
            logger.warning("Failed to fetch capabilities history for %s: %s", agent_name, e)
            return []

    async def get_routing_table(self) -> dict:
        """Derive routing table from current registered modules.

        Returns a mapping of capability -> list of agents that provide it.
        """
        table: dict[str, list[str]] = {}
        for module in self.get_online_modules():
            for cap in module.capabilities:
                if cap not in table:
                    table[cap] = []
                table[cap].append(module.name)

        return {
            "routing": table,
            "last_updated": (
                self._last_discovery.isoformat() if self._last_discovery else None
            ),
            "total_modules": self.total_modules,
            "online_modules": self.online_count,
        }

    async def get_all_modules_dict(self) -> list[dict]:
        """Get all modules as dicts (for API responses)."""
        return [m.to_dict() for m in self._modules.values()]

    async def load_from_db(self) -> int:
        """Load modules from DB into memory (startup recovery).

        Returns count of modules loaded.
        """
        if not self._db:
            return 0

        try:
            db_modules = await self._db.get_all_modules()
            loaded = 0
            for m in db_modules:
                status_map = {
                    "healthy": ModuleStatus.ONLINE,
                    "degraded": ModuleStatus.DEGRADED,
                    "unhealthy": ModuleStatus.OFFLINE,
                    "unknown": ModuleStatus.OFFLINE,
                }
                self._modules[m.agent_name] = ModuleInfo(
                    name=m.agent_name,
                    base_url=m.base_url,
                    version=m.version,
                    description=m.description or "",
                    capabilities=m.capabilities if isinstance(m.capabilities, list) else [],
                    status=status_map.get(m.health_status, ModuleStatus.OFFLINE),
                    last_check=m.last_seen_at or datetime.now(),
                )
                loaded += 1

            logger.info("Loaded %d modules from database", loaded)
            return loaded
        except Exception as e:
            logger.warning("Failed to load modules from DB: %s (starting fresh)", e)
            return 0
