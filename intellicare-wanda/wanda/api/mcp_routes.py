"""MCP API routes — /api/v1/mcp/* (EF-W011).

Endpoints for managing MCP Server connections,
listing tools, and direct tool invocation (admin).
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])

# Injected by app.py at startup
_mcp_client = None
_tool_registry = None


def init_mcp_routes(mcp_client, tool_registry=None) -> None:
    """Initialize dependencies (called from app.py)."""
    global _mcp_client, _tool_registry
    _mcp_client = mcp_client
    _tool_registry = tool_registry


class ToolCallRequest(BaseModel):
    params: dict = {}
    correlation_id: Optional[str] = None


@router.get("/modules")
async def list_mcp_modules():
    """List all registered MCP Servers and their status."""
    if _mcp_client is None:
        raise HTTPException(status_code=503, detail="MCP client not initialized")

    records = _mcp_client.get_all_module_records()
    return {
        "success": True,
        "data": {
            "modules": [r.to_dict() for r in records],
            "total": len(records),
            "connected": len(_mcp_client.connected_modules),
        },
    }


@router.get("/modules/{module_name}/tools")
async def list_module_tools(module_name: str):
    """List tools available from a specific MCP Server."""
    if _mcp_client is None:
        raise HTTPException(status_code=503, detail="MCP client not initialized")

    tools = await _mcp_client.list_tools(module_name)
    module_tools = tools.get(module_name, [])

    if not module_tools:
        record = _mcp_client.get_module_record(module_name)
        if not record:
            raise HTTPException(
                status_code=404, detail=f"MCP module {module_name} not found"
            )

    return {
        "success": True,
        "data": {
            "module_name": module_name,
            "tools": module_tools,
            "count": len(module_tools),
        },
    }


@router.post("/modules/{module_name}/refresh")
async def refresh_module_tools(module_name: str):
    """Re-discover tools from an MCP Server (admin)."""
    if _mcp_client is None:
        raise HTTPException(status_code=503, detail="MCP client not initialized")

    try:
        tools = await _mcp_client.refresh_tools(module_name)
        return {
            "success": True,
            "data": {
                "module_name": module_name,
                "tools": [t.to_dict() for t in tools],
                "count": len(tools),
                "refreshed_at": tools[0].last_validated.isoformat() if tools else None,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Failed to refresh tools for {module_name}: {e}"
        )


@router.post("/tools/{module_name}/{tool_name}")
async def call_mcp_tool(
    module_name: str,
    tool_name: str,
    req: ToolCallRequest,
):
    """Execute an MCP tool directly (admin/debug endpoint)."""
    if _mcp_client is None:
        raise HTTPException(status_code=503, detail="MCP client not initialized")

    try:
        result = await _mcp_client.call_tool(
            module_name=module_name,
            tool_name=tool_name,
            params=req.params,
            correlation_id=req.correlation_id,
        )
        return {
            "success": True,
            "data": {
                "result": result,
                "module_name": module_name,
                "tool_name": tool_name,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/tools")
async def list_all_tools():
    """List all available tools across all MCP Servers."""
    if _mcp_client is None:
        raise HTTPException(status_code=503, detail="MCP client not initialized")

    all_tools = await _mcp_client.list_tools()
    flat_tools = []
    for module_name, tools in all_tools.items():
        for tool in tools:
            tool["module_name"] = module_name
            flat_tools.append(tool)

    return {
        "success": True,
        "data": {
            "tools": flat_tools,
            "total": len(flat_tools),
        },
    }
