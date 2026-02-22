"""Data models for MCP subsystem (EF-W011)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4


@dataclass
class MCPToolInfo:
    """Description of a tool provided by an MCP Server."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    module_name: str = ""
    last_validated: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "module_name": self.module_name,
            "last_validated": (
                self.last_validated.isoformat() if self.last_validated else None
            ),
        }


@dataclass
class MCPModuleRecord:
    """Registration record for an MCP Server."""

    module_name: str
    agent_name: str
    base_url: str
    mcp_endpoint: str = "/mcp/sse"
    status: str = "healthy"  # healthy, degraded, unavailable

    available_tools: list[MCPToolInfo] = field(default_factory=list)

    last_health_check: Optional[datetime] = None
    last_tools_discovery: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def tools_count(self) -> int:
        return len(self.available_tools)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "agent_name": self.agent_name,
            "base_url": self.base_url,
            "mcp_endpoint": self.mcp_endpoint,
            "status": self.status,
            "tools_count": self.tools_count,
            "tools": [t.to_dict() for t in self.available_tools],
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "last_tools_discovery": (
                self.last_tools_discovery.isoformat()
                if self.last_tools_discovery
                else None
            ),
        }


@dataclass
class MCPCallRecord:
    """Audit record of an MCP tool invocation."""

    correlation_id: str
    module_name: str
    tool_name: str

    input_params: dict[str, Any] = field(default_factory=dict)
    output_summary: str = ""

    status: str = "success"  # success, error, timeout
    error_message: str = ""

    duration_ms: int = 0
    tokens_used: Optional[int] = None

    called_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "module_name": self.module_name,
            "tool_name": self.tool_name,
            "status": self.status,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "called_at": self.called_at.isoformat(),
        }
