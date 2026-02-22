"""
MultiMCPToolProvider — Agregador de ferramentas de múltiplos MCP endpoints
Inspirado no FHIR-AgentEval (tool_providers.py)
"""

from typing import Any, Dict, List, Optional
from wanda.mcp.client import WandaMCPClient
from wanda.mcp.tool_registry import ToolDefinition

class MultiMCPToolProvider:
    """
    Agrega ferramentas de múltiplos WandaMCPClient.
    Resolve conflitos de nomes automaticamente.
    """
    def __init__(self, mcp_clients: List[WandaMCPClient]):
        self._clients = mcp_clients
        self._tools: Dict[str, ToolDefinition] = {}

    async def build(self) -> None:
        """Constrói o registro de ferramentas agregando todos os MCP endpoints."""
        self._tools.clear()
        seen_names = set()
        for idx, client in enumerate(self._clients):
            await client.connect_all()
            registry = ToolDefinition
            all_tools = await client.list_tools()
            for module_name, tools in all_tools.items():
                for tool_dict in tools:
                    tool_name = tool_dict["name"]
                    # Resolve conflito de nome
                    if tool_name in seen_names:
                        prefixed_name = f"{module_name}_{tool_name}"
                    else:
                        prefixed_name = tool_name
                        seen_names.add(tool_name)
                    description = tool_dict.get("description", "")
                    async def make_invoker(mn: str, tn: str):
                        async def invoke(params: dict, correlation_id: str = "") -> dict:
                            return await client.call_tool(
                                module_name=mn,
                                tool_name=tn,
                                params=params,
                                correlation_id=correlation_id,
                            )
                        return invoke
                    invoker = await make_invoker(module_name, tool_name)
                    self._tools[prefixed_name] = ToolDefinition(
                        name=prefixed_name,
                        description=description,
                        source_type="mcp",
                        module_name=module_name,
                        invoke=invoker,
                    )

    def get_all_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_tools_by_module(self, module_name: str) -> List[ToolDefinition]:
        return [t for t in self._tools.values() if t.module_name == module_name]

    @property
    def total_tools(self) -> int:
        return len(self._tools)
