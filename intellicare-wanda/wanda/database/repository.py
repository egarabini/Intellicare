"""Repository layer for persistent module registry (EF-W001)."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wanda.database.models import (
    MCPCallLogModel,
    MCPModuleModel,
    MCPToolModel,
    ModuleCapabilitiesHistoryModel,
    ModuleHealthEventModel,
    OrchestrationExecutionModel,
    RegisteredModuleModel,
)

logger = logging.getLogger(__name__)


class ModuleRepository:
    """CRUD operations for the persistent module registry.

    All methods receive an async session and operate within transactions.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    # ── Registered Modules ─────────────────────────────────────────

    async def register_or_update(self, module_info: dict) -> RegisteredModuleModel:
        """Register a new module or update an existing one.

        If the module exists and capabilities changed, bump capabilities_version.
        """
        async with self._session_factory() as session:
            agent_name = module_info["agent_name"]
            stmt = select(RegisteredModuleModel).where(
                RegisteredModuleModel.agent_name == agent_name
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            now = datetime.now(timezone.utc)

            if existing is None:
                # New module
                module = RegisteredModuleModel(
                    agent_name=agent_name,
                    module_type=module_info.get("module_type", "HTTP"),
                    version=module_info.get("version", "0.0.0"),
                    description=module_info.get("description", ""),
                    base_url=module_info.get("base_url", ""),
                    port=module_info.get("port", 0),
                    status="active",
                    health_status="healthy",
                    capabilities=module_info.get("capabilities", []),
                    capabilities_version=1,
                    requires_patient_context=module_info.get(
                        "requires_patient_context", False
                    ),
                    supports_ips_first=module_info.get("supports_ips_first", False),
                    endpoints=module_info.get("endpoints", {}),
                    first_seen_at=now,
                    last_seen_at=now,
                    last_health_check_at=now,
                    created_at=now,
                    updated_at=now,
                )
                session.add(module)
                await session.commit()
                await session.refresh(module)
                logger.info("Registered new module: %s", agent_name)
                return module
            else:
                # Update existing
                old_caps = existing.capabilities
                new_caps = module_info.get("capabilities", old_caps)
                caps_changed = sorted(str(c) for c in old_caps) != sorted(
                    str(c) for c in new_caps
                )

                existing.version = module_info.get("version", existing.version)
                existing.description = module_info.get(
                    "description", existing.description
                )
                existing.base_url = module_info.get("base_url", existing.base_url)
                existing.port = module_info.get("port", existing.port)
                existing.status = "active"
                existing.health_status = "healthy"
                existing.last_seen_at = now
                existing.last_health_check_at = now
                existing.updated_at = now

                if caps_changed:
                    existing.capabilities = new_caps
                    existing.capabilities_version += 1
                    # Record capability history
                    history = ModuleCapabilitiesHistoryModel(
                        agent_name=agent_name,
                        version=existing.capabilities_version,
                        capabilities=new_caps,
                        changed_at=now,
                        change_type="modified",
                    )
                    session.add(history)

                await session.commit()
                await session.refresh(existing)
                logger.info("Updated module: %s (caps_changed=%s)", agent_name, caps_changed)
                return existing

    async def get_active_modules(self) -> list[RegisteredModuleModel]:
        """Return modules with status=active and health_status=healthy."""
        async with self._session_factory() as session:
            stmt = select(RegisteredModuleModel).where(
                RegisteredModuleModel.status == "active",
                RegisteredModuleModel.health_status.in_(["healthy", "degraded"]),
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_modules(self) -> list[RegisteredModuleModel]:
        """Return all registered modules."""
        async with self._session_factory() as session:
            stmt = select(RegisteredModuleModel)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_module(self, agent_name: str) -> Optional[RegisteredModuleModel]:
        """Get a module by agent name."""
        async with self._session_factory() as session:
            stmt = select(RegisteredModuleModel).where(
                RegisteredModuleModel.agent_name == agent_name
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_modules_with_capability(
        self, capability_id: str
    ) -> list[RegisteredModuleModel]:
        """Return active modules that have a specific capability."""
        modules = await self.get_active_modules()
        return [m for m in modules if capability_id in (m.capabilities or [])]

    async def mark_unhealthy(self, agent_name: str, reason: str) -> None:
        """Mark a module as unhealthy (preserves history)."""
        async with self._session_factory() as session:
            stmt = select(RegisteredModuleModel).where(
                RegisteredModuleModel.agent_name == agent_name
            )
            result = await session.execute(stmt)
            module = result.scalar_one_or_none()

            if module:
                now = datetime.now(timezone.utc)
                old_status = module.health_status

                module.health_status = "unhealthy"
                module.last_health_check_at = now
                module.updated_at = now

                # Record health event
                event = ModuleHealthEventModel(
                    agent_name=agent_name,
                    event_type="went_unhealthy",
                    previous_status=old_status,
                    new_status="unhealthy",
                    reason=reason,
                    occurred_at=now,
                )
                session.add(event)
                await session.commit()
                logger.warning("Module %s marked unhealthy: %s", agent_name, reason)

    async def mark_healthy(self, agent_name: str) -> None:
        """Restore a module to healthy status."""
        async with self._session_factory() as session:
            stmt = select(RegisteredModuleModel).where(
                RegisteredModuleModel.agent_name == agent_name
            )
            result = await session.execute(stmt)
            module = result.scalar_one_or_none()

            if module and module.health_status != "healthy":
                now = datetime.now(timezone.utc)
                old_status = module.health_status

                module.health_status = "healthy"
                module.last_health_check_at = now
                module.updated_at = now

                event = ModuleHealthEventModel(
                    agent_name=agent_name,
                    event_type="went_healthy",
                    previous_status=old_status,
                    new_status="healthy",
                    occurred_at=now,
                )
                session.add(event)
                await session.commit()
                logger.info("Module %s restored to healthy", agent_name)

    async def get_health_history(
        self, agent_name: str, last_n_events: int = 50
    ) -> list[ModuleHealthEventModel]:
        """Health event history for a module."""
        async with self._session_factory() as session:
            stmt = (
                select(ModuleHealthEventModel)
                .where(ModuleHealthEventModel.agent_name == agent_name)
                .order_by(ModuleHealthEventModel.occurred_at.desc())
                .limit(last_n_events)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_capabilities_history(
        self, agent_name: str, last_n: int = 20
    ) -> list[ModuleCapabilitiesHistoryModel]:
        """Capabilities version history for a module."""
        async with self._session_factory() as session:
            stmt = (
                select(ModuleCapabilitiesHistoryModel)
                .where(ModuleCapabilitiesHistoryModel.agent_name == agent_name)
                .order_by(ModuleCapabilitiesHistoryModel.changed_at.desc())
                .limit(last_n)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ── Orchestration Executions ───────────────────────────────────

    async def log_execution(self, execution_data: dict) -> OrchestrationExecutionModel:
        """Log an orchestration execution."""
        async with self._session_factory() as session:
            execution = OrchestrationExecutionModel(**execution_data)
            session.add(execution)
            await session.commit()
            await session.refresh(execution)
            return execution

    # ── MCP Modules ────────────────────────────────────────────────

    async def register_mcp_module(self, mcp_data: dict) -> MCPModuleModel:
        """Register or update an MCP Server."""
        async with self._session_factory() as session:
            stmt = select(MCPModuleModel).where(
                MCPModuleModel.module_name == mcp_data["module_name"]
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            now = datetime.now(timezone.utc)

            if existing is None:
                module = MCPModuleModel(
                    module_name=mcp_data["module_name"],
                    agent_name=mcp_data["agent_name"],
                    base_url=mcp_data["base_url"],
                    mcp_endpoint=mcp_data.get("mcp_endpoint", "/mcp/sse"),
                    status=mcp_data.get("status", "healthy"),
                    tools_count=mcp_data.get("tools_count", 0),
                    last_health_check=now,
                    last_tools_discovery=now,
                    created_at=now,
                    updated_at=now,
                )
                session.add(module)
                await session.commit()
                await session.refresh(module)
                return module
            else:
                existing.status = mcp_data.get("status", existing.status)
                existing.tools_count = mcp_data.get("tools_count", existing.tools_count)
                existing.base_url = mcp_data.get("base_url", existing.base_url)
                existing.last_health_check = now
                existing.last_tools_discovery = now
                existing.updated_at = now
                await session.commit()
                await session.refresh(existing)
                return existing

    async def get_mcp_modules(self) -> list[MCPModuleModel]:
        """Return all MCP modules."""
        async with self._session_factory() as session:
            stmt = select(MCPModuleModel)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_mcp_module(self, module_name: str) -> Optional[MCPModuleModel]:
        """Get an MCP module by name."""
        async with self._session_factory() as session:
            stmt = select(MCPModuleModel).where(
                MCPModuleModel.module_name == module_name
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def register_mcp_tools(
        self, module_id: UUID, tools: list[dict]
    ) -> list[MCPToolModel]:
        """Register tools for an MCP module (replace all)."""
        async with self._session_factory() as session:
            # Delete existing tools for this module
            from sqlalchemy import delete

            await session.execute(
                delete(MCPToolModel).where(MCPToolModel.module_id == module_id)
            )

            now = datetime.now(timezone.utc)
            new_tools = []
            for tool_data in tools:
                tool = MCPToolModel(
                    module_id=module_id,
                    tool_name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("input_schema", {}),
                    last_validated=now,
                )
                session.add(tool)
                new_tools.append(tool)

            await session.commit()
            for t in new_tools:
                await session.refresh(t)
            return new_tools

    async def get_mcp_tools(self, module_id: UUID) -> list[MCPToolModel]:
        """Get tools for an MCP module."""
        async with self._session_factory() as session:
            stmt = select(MCPToolModel).where(MCPToolModel.module_id == module_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ── MCP Call Log ───────────────────────────────────────────────

    async def log_mcp_call(self, call_data: dict) -> MCPCallLogModel:
        """Log an MCP tool invocation."""
        async with self._session_factory() as session:
            log_entry = MCPCallLogModel(**call_data)
            session.add(log_entry)
            await session.commit()
            await session.refresh(log_entry)
            return log_entry
