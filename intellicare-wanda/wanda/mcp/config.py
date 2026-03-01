"""MCP Client configuration (EF-W011)."""

from typing import Any

from pydantic import BaseModel, Field


class MCPClientConfig(BaseModel):
    """Configuration for WANDA's MCP Client connections."""

    # MCP Server URLs
    mcp_servers: dict[str, str] = Field(
        default_factory=lambda: {
            "intellicare-minerva": "http://intellicare-minerva:8008",
            "intellicare-superz": "http://intellicare-pierre:8009",
        }
    )

    # Agent names (for display)
    mcp_agent_names: dict[str, str] = Field(
        default_factory=lambda: {
            "intellicare-minerva": "MINERVA",
            "intellicare-superz": "PIERRE",
        }
    )

    # Per-module tool discovery path (GET)
    # MINERVA: /mcp/tools  |  PIERRE: /api/v1/mcp/tools
    mcp_tool_list_paths: dict[str, str] = Field(
        default_factory=lambda: {
            "intellicare-minerva": "/mcp/tools",
            "intellicare-superz": "/api/v1/mcp/tools",
        }
    )

    # Per-module tool call style:
    #   "path_params" → POST {base_url}/mcp/tools/{tool_name}  body = params dict
    #   "body_named"  → POST {base_url}/api/v1/mcp/call        body = {"name": tool_name, "arguments": params}
    mcp_tool_call_style: dict[str, str] = Field(
        default_factory=lambda: {
            "intellicare-minerva": "path_params",
            "intellicare-superz": "body_named",
        }
    )

    # Per-module call base path (for "path_params" style, /{tool_name} is appended)
    mcp_tool_call_paths: dict[str, str] = Field(
        default_factory=lambda: {
            "intellicare-minerva": "/mcp/tools",
            "intellicare-superz": "/api/v1/mcp/call",
        }
    )

    # Timeouts by tool category
    minerva_timeout_seconds: int = 30  # OCR can be slow (large PDFs)
    search_timeout_seconds: int = 15  # Web search
    analysis_timeout_seconds: int = 60  # LLM text analysis (Qwen2.5-72B)
    default_timeout_seconds: int = 30

    # Connection
    connection_timeout_seconds: int = 10

    # Retry policy
    max_retries: int = 2
    retry_delay_seconds: float = 1.0

    def get_list_url(self, module_name: str, base_url: str) -> str:
        """Return the full URL for tool discovery."""
        path = self.mcp_tool_list_paths.get(module_name, "/mcp/tools")
        return f"{base_url}{path}"

    def get_call_url_and_body(
        self, module_name: str, base_url: str, tool_name: str, params: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Return (url, request_body) for a tool invocation.

        Returns:
            (url, body) — body format depends on the module's call style.
        """
        style = self.mcp_tool_call_style.get(module_name, "path_params")
        call_path = self.mcp_tool_call_paths.get(module_name, "/mcp/tools")

        if style == "body_named":
            # PIERRE: POST /api/v1/mcp/call  {"name": "...", "arguments": {...}}
            url = f"{base_url}{call_path}"
            body: dict[str, Any] = {"name": tool_name, "arguments": params}
        else:
            # MINERVA (default): POST /mcp/tools/{tool_name}  body = params dict
            url = f"{base_url}{call_path}/{tool_name}"
            body = params

        return url, body

    def get_timeout_for_tool(self, module_name: str, tool_name: str) -> int:
        """Get the appropriate timeout for a tool."""
        # OCR tools
        if module_name == "intellicare-minerva":
            return self.minerva_timeout_seconds

        # SuperZ tools
        if tool_name in ("web_search", "search_medical_literature", "check_regulatory"):
            return self.search_timeout_seconds
        if tool_name in ("analyze_text", "summarize_document"):
            return self.analysis_timeout_seconds

        return self.default_timeout_seconds
