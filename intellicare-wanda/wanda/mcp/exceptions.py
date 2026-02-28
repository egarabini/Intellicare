"""MCP-specific exception hierarchy (EF-W011)."""


class MCPError(Exception):
    """Base exception for MCP operations."""

    pass


class MCPModuleUnavailableError(MCPError):
    """MCP Server is not connected or unavailable."""

    def __init__(self, module_name: str, detail: str = ""):
        self.module_name = module_name
        msg = f"MCP module {module_name} is unavailable"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


class MCPToolNotFoundError(MCPError):
    """MCP tool does not exist on the server."""

    def __init__(self, module_name: str, tool_name: str):
        self.module_name = module_name
        self.tool_name = tool_name
        super().__init__(
            f"Tool '{tool_name}' not found on MCP module '{module_name}'"
        )


class MCPCallTimeoutError(MCPError):
    """MCP tool call timed out."""

    def __init__(self, module_name: str, tool_name: str, timeout_seconds: int):
        self.module_name = module_name
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"MCP tool {module_name}/{tool_name} timed out after {timeout_seconds}s"
        )


class MCPCallError(MCPError):
    """MCP tool call returned an error."""

    def __init__(self, module_name: str, tool_name: str, detail: str = ""):
        self.module_name = module_name
        self.tool_name = tool_name
        msg = f"MCP tool {module_name}/{tool_name} failed"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
