"""FastAPI app — endpoints REST + MCP SSE transport."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from superz import __version__
from superz.config import SuperZConfig
from superz.mcp.server import SuperZMCPServer

logger = logging.getLogger(__name__)

# Globals (initialized in lifespan)
_mcp_server: SuperZMCPServer | None = None
_config: SuperZConfig | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    global _mcp_server, _config

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    _config = SuperZConfig.from_env()
    _mcp_server = SuperZMCPServer(_config)
    logger.info(
        "SuperZ/PIERRE iniciado — Tavily=%s, LLM=%s, Redis=%s",
        "configurado" if _config.tavily_configured else "NAO configurado",
        _config.llm_model,
        _config.redis_url,
    )
    yield
    if _mcp_server:
        await _mcp_server.shutdown()
    logger.info("SuperZ/PIERRE encerrado")


app = FastAPI(
    title="intellicare-superz",
    description="MCP Server de inteligencia externa do IntelliCare (PIERRE)",
    version=__version__,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────
# Health & Info
# ──────────────────────────────────────

@app.get("/api/v1/health")
async def health() -> JSONResponse:
    """Health check detalhado — status de cada componente."""
    if _mcp_server is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "message": "Server nao inicializado"},
        )

    health_data = await _mcp_server.get_health()
    status_code = 200 if health_data["status"] == "healthy" else 207
    return JSONResponse(status_code=status_code, content=health_data)


@app.get("/api/v1/info")
async def info() -> dict[str, Any]:
    """Metadata do modulo."""
    return {
        "module": "intellicare-superz",
        "agent": "PIERRE (Pierre Curie)",
        "version": __version__,
        "description": "MCP Server de inteligencia externa — busca web, literatura medica, "
                       "regulatorio, analise LLM, resumo, traducao",
        "port": _config.port if _config else 8009,
        "tools": [
            "web_search",
            "search_medical_literature",
            "check_regulatory",
            "analyze_text",
            "summarize_document",
            "translate_to_portuguese",
        ],
        "tools_count": 6,
        "stack": {
            "search": ["Tavily", "PubMed", "BIREME", "SciELO"],
            "llm": _config.llm_model if _config else "qwen2.5:72b",
            "cache": "Redis",
            "knowledge": "enabled" if _config and _config.enable_knowledge_integration else "disabled",
        },
    }


# ──────────────────────────────────────
# MCP over SSE endpoints
# ──────────────────────────────────────

@app.get("/api/v1/mcp/tools")
async def list_tools() -> dict[str, Any]:
    """Lista as MCP tools disponiveis (REST wrapper)."""
    if _mcp_server is None:
        return {"tools": [], "error": "Server nao inicializado"}

    # Acessa diretamente o handler registrado
    tools = await _mcp_server.server.request_handlers.get("tools/list", lambda: {"tools": []})()
    tool_list = []
    if hasattr(tools, "tools"):
        for t in tools.tools:
            tool_list.append({
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema,
            })

    return {"tools": tool_list, "count": len(tool_list)}


@app.post("/api/v1/mcp/call")
async def call_tool(request: Request) -> JSONResponse:
    """Chama uma MCP tool via REST (wrapper para desenvolvimento/teste)."""
    if _mcp_server is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Server nao inicializado"},
        )

    body = await request.json()
    tool_name = body.get("name", "")
    arguments = body.get("arguments", {})

    if not tool_name:
        return JSONResponse(
            status_code=400,
            content={"error": "Campo 'name' obrigatorio"},
        )

    try:
        result = await _mcp_server._route_tool(tool_name, arguments)
        return JSONResponse(content=result)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        logger.error("call_tool %s falhou: %s", tool_name, e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "tool": tool_name},
        )


# ──────────────────────────────────────
# Rate limiter status
# ──────────────────────────────────────

@app.get("/api/v1/rate-limit")
async def rate_limit_status() -> dict[str, Any]:
    """Status do rate limiter Tavily."""
    if _mcp_server is None:
        return {"error": "Server nao inicializado"}
    return await _mcp_server._rate_limiter.get_status()
