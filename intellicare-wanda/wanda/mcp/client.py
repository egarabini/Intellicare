"""WANDA MCP Client — consumes MINERVA and PIERRE MCP Servers (EF-W011).

Manages SSE sessions to MCP Servers and provides tool invocation.
Uses HTTP REST as fallback when SSE is unavailable.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx

from wanda.mcp.config import MCPClientConfig
from wanda.mcp.exceptions import (
    MCPCallError,
    MCPCallTimeoutError,
    MCPModuleUnavailableError,
    MCPToolNotFoundError,
)
from wanda.mcp.models import MCPCallRecord, MCPModuleRecord, MCPToolInfo

logger = logging.getLogger(__name__)

# Degradation policy
DEGRADATION_POLICY: dict[str, dict[str, Any]] = {
    "intellicare-ocr": {
        "fallback_message": (
            "Servico de OCR (MINERVA) indisponivel. "
            "Nao e possivel processar documentos no momento. "
            "Tente novamente em alguns minutos."
        ),
        "can_continue_without": True,
        "tools_affected": [
            "extract_document",
            "ocr_image",
            "parse_lab_result",
            "parse_discharge_summary",
            "search_documents",
            "index_document",
        ],
    },
    "intellicare-superz": {
        "fallback_message": (
            "Servico de pesquisa externa (PIERRE) indisponivel. "
            "Usando apenas conhecimento dos agentes clinicos locais. "
            "Informacoes podem nao refletir guidelines mais recentes."
        ),
        "can_continue_without": True,
        "tools_affected": [
            "web_search",
            "search_medical_literature",
            "check_regulatory",
            "analyze_text",
            "summarize_document",
            "translate_to_portuguese",
        ],
    },
}


class WandaMCPClient:
    """MCP Client for WANDA to consume MINERVA and PIERRE.

    Uses HTTP REST fallback (POST /mcp/tools/{tool_name}) since
    SSE session management is complex. The REST fallback is the
    recommended approach for WANDA's use case.
    """

    def __init__(
        self,
        config: Optional[MCPClientConfig] = None,
        db_repository: Optional[Any] = None,
    ):
        self._config = config or MCPClientConfig()
        self._db = db_repository
        self._connected: dict[str, bool] = {}
        self._tools_cache: dict[str, list[MCPToolInfo]] = {}
        self._module_records: dict[str, MCPModuleRecord] = {}
        self._call_log: list[MCPCallRecord] = []

    @property
    def connected_modules(self) -> list[str]:
        """Return names of connected MCP modules."""
        return [name for name, connected in self._connected.items() if connected]

    async def connect_all(self) -> dict[str, bool]:
        """Connect to all configured MCP Servers.

        Probes health and discovers tools for each server.
        Returns: { module_name: success_bool }
        """
        results: dict[str, bool] = {}

        for module_name, base_url in self._config.mcp_servers.items():
            try:
                # Check health
                healthy = await self.health_check(module_name)
                if not healthy:
                    results[module_name] = False
                    self._connected[module_name] = False
                    continue

                # Discover tools
                tools = await self._discover_tools(module_name, base_url)
                self._tools_cache[module_name] = tools

                # Build module record
                agent_name = self._config.mcp_agent_names.get(module_name, module_name)
                self._module_records[module_name] = MCPModuleRecord(
                    module_name=module_name,
                    agent_name=agent_name,
                    base_url=base_url,
                    status="healthy",
                    available_tools=tools,
                    last_health_check=datetime.now(),
                    last_tools_discovery=datetime.now(),
                )
                self._connected[module_name] = True
                results[module_name] = True

                logger.info(
                    "MCP connected: %s (%s) — %d tools",
                    module_name,
                    agent_name,
                    len(tools),
                )

                # Persist to DB if available
                if self._db:
                    try:
                        db_module = await self._db.register_mcp_module(
                            {
                                "module_name": module_name,
                                "agent_name": agent_name,
                                "base_url": base_url,
                                "status": "healthy",
                                "tools_count": len(tools),
                            }
                        )
                        await self._db.register_mcp_tools(
                            db_module.id,
                            [t.to_dict() for t in tools],
                        )
                    except Exception as e:
                        logger.warning("Failed to persist MCP module %s: %s", module_name, e)

            except Exception as e:
                logger.warning("MCP connection failed: %s — %s", module_name, e)
                results[module_name] = False
                self._connected[module_name] = False

        return results

    async def call_tool(
        self,
        module_name: str,
        tool_name: str,
        params: dict[str, Any],
        correlation_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> dict[str, Any]:
        """Call an MCP tool and return the result.

        Uses HTTP REST fallback: POST /mcp/tools/{tool_name}
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        if not self._connected.get(module_name):
            raise MCPModuleUnavailableError(
                module_name,
                f"Ensure {module_name} is running and accessible.",
            )

        # Validate tool exists
        tools = self._tools_cache.get(module_name, [])
        tool_exists = any(t.name == tool_name for t in tools)
        if not tool_exists:
            raise MCPToolNotFoundError(module_name, tool_name)

        if timeout_seconds is None:
            timeout_seconds = self._config.get_timeout_for_tool(module_name, tool_name)

        base_url = self._config.mcp_servers[module_name]
        url, body = self._config.get_call_url_and_body(module_name, base_url, tool_name, params)

        started_at = time.monotonic()
        retries = 0

        while retries <= self._config.max_retries:
            try:
                async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                    resp = await client.post(url, json=body)

                    duration_ms = int((time.monotonic() - started_at) * 1000)

                    if resp.status_code == 200:
                        result = resp.json()
                        await self._log_call(
                            correlation_id=correlation_id,
                            module_name=module_name,
                            tool_name=tool_name,
                            params=params,
                            status="success",
                            duration_ms=duration_ms,
                        )
                        return result
                    else:
                        error_msg = resp.text
                        if retries >= self._config.max_retries:
                            await self._log_call(
                                correlation_id=correlation_id,
                                module_name=module_name,
                                tool_name=tool_name,
                                params=params,
                                status="error",
                                error_message=error_msg,
                                duration_ms=duration_ms,
                            )
                            raise MCPCallError(module_name, tool_name, error_msg)

            except httpx.TimeoutException:
                duration_ms = int((time.monotonic() - started_at) * 1000)
                if retries >= self._config.max_retries:
                    await self._log_call(
                        correlation_id=correlation_id,
                        module_name=module_name,
                        tool_name=tool_name,
                        params=params,
                        status="timeout",
                        duration_ms=duration_ms,
                    )
                    raise MCPCallTimeoutError(module_name, tool_name, timeout_seconds)

            except (MCPCallError, MCPCallTimeoutError):
                raise

            except httpx.RequestError as e:
                duration_ms = int((time.monotonic() - started_at) * 1000)
                if retries >= self._config.max_retries:
                    await self._log_call(
                        correlation_id=correlation_id,
                        module_name=module_name,
                        tool_name=tool_name,
                        params=params,
                        status="error",
                        error_message=str(e),
                        duration_ms=duration_ms,
                    )
                    raise MCPCallError(module_name, tool_name, str(e))

            retries += 1
            if retries <= self._config.max_retries:
                await asyncio.sleep(self._config.retry_delay_seconds)

        # Should not reach here, but just in case
        raise MCPCallError(module_name, tool_name, "Max retries exceeded")

    async def list_tools(
        self, module_name: Optional[str] = None
    ) -> dict[str, list[dict[str, Any]]]:
        """List tools from MCP Servers.

        Args:
            module_name: None = all modules.

        Returns:
            { module_name: [tool_dicts...] }
        """
        if module_name:
            tools = self._tools_cache.get(module_name, [])
            return {module_name: [t.to_dict() for t in tools]}

        return {
            name: [t.to_dict() for t in tools]
            for name, tools in self._tools_cache.items()
        }

    async def refresh_tools(self, module_name: str) -> list[MCPToolInfo]:
        """Re-discover tools from an MCP Server."""
        base_url = self._config.mcp_servers.get(module_name)
        if not base_url:
            raise MCPModuleUnavailableError(module_name, "Unknown module")

        tools = await self._discover_tools(module_name, base_url)
        self._tools_cache[module_name] = tools

        # Update record
        if module_name in self._module_records:
            self._module_records[module_name].available_tools = tools
            self._module_records[module_name].last_tools_discovery = datetime.now()

        logger.info("Refreshed tools for %s: %d tools", module_name, len(tools))
        return tools

    async def health_check(self, module_name: str) -> bool:
        """Check if an MCP Server is responding."""
        base_url = self._config.mcp_servers.get(module_name)
        if not base_url:
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base_url}/api/v1/health")
                return resp.status_code == 200
        except Exception:
            return False

    def get_module_record(self, module_name: str) -> Optional[MCPModuleRecord]:
        """Get the module record for an MCP server."""
        return self._module_records.get(module_name)

    def get_all_module_records(self) -> list[MCPModuleRecord]:
        """Get all known MCP module records."""
        return list(self._module_records.values())

    def get_degradation_message(self, module_name: str) -> str:
        """Get the degradation message for an unavailable module."""
        policy = DEGRADATION_POLICY.get(module_name, {})
        return policy.get("fallback_message", f"MCP module {module_name} is unavailable.")

    def can_continue_without(self, module_name: str) -> bool:
        """Whether WANDA can continue if this module is unavailable."""
        policy = DEGRADATION_POLICY.get(module_name, {})
        return policy.get("can_continue_without", True)

    # ── Private ────────────────────────────────────────────────────

    async def _discover_tools(
        self, module_name: str, base_url: str
    ) -> list[MCPToolInfo]:
        """Discover tools from an MCP Server using per-module configured path."""
        url = self._config.get_list_url(module_name, base_url)
        try:
            async with httpx.AsyncClient(timeout=self._config.connection_timeout_seconds) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    tools_data = data if isinstance(data, list) else data.get("tools", [])
                    tools = []
                    for td in tools_data:
                        tools.append(
                            MCPToolInfo(
                                name=td.get("name", ""),
                                description=td.get("description", ""),
                                input_schema=td.get("inputSchema", td.get("input_schema", {})),
                                module_name=module_name,
                                last_validated=datetime.now(),
                            )
                        )
                    return tools
        except Exception as e:
            logger.warning("Failed to discover tools from %s: %s", module_name, e)
        return []

    async def _log_call(
        self,
        correlation_id: str,
        module_name: str,
        tool_name: str,
        params: dict,
        status: str,
        duration_ms: int,
        error_message: str = "",
    ) -> None:
        """Log an MCP tool call."""
        record = MCPCallRecord(
            correlation_id=correlation_id,
            module_name=module_name,
            tool_name=tool_name,
            input_params=self._sanitize_params(params),
            status=status,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        self._call_log.append(record)

        # Persist to DB if available
        if self._db:
            try:
                await self._db.log_mcp_call(
                    {
                        "correlation_id": correlation_id,
                        "module_name": module_name,
                        "tool_name": tool_name,
                        "input_summary": json.dumps(self._sanitize_params(params)),
                        "status": status,
                        "error_message": error_message or None,
                        "duration_ms": duration_ms,
                    }
                )
            except Exception as e:
                logger.warning("Failed to persist MCP call log: %s", e)

    def _sanitize_params(self, params: dict) -> dict:
        """Remove sensitive data from params for logging."""
        sanitized = {}
        for key, value in params.items():
            if any(
                sensitive in key.lower()
                for sensitive in ("base64", "content", "file", "image", "password")
            ):
                sanitized[key] = f"<{type(value).__name__}:{len(str(value))} chars>"
            else:
                sanitized[key] = value
        return sanitized
