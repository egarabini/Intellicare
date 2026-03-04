"""FastAPI app — endpoints REST + MCP SSE transport."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from pierre import __version__
from pierre.config import PierreConfig
from pierre.mcp.server import PierreMCPServer

logger = logging.getLogger(__name__)

# Globals (initialized in lifespan)
_mcp_server: PierreMCPServer | None = None
_config: PierreConfig | None = None


class AnalyzeRequest(BaseModel):
    """Request padrao BaseAgent para orquestracao via Wanda."""

    patient_id: str
    query: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


def _resolve_tool_payload(query: str, parameters: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Mapeia capability de alto nivel para uma tool MCP do PIERRE."""
    capability = str(parameters.get("capability", "")).strip().lower()

    if capability in {"medical_literature", "search_medical_literature", "literature"}:
        return "search_medical_literature", {
            "query": query,
            "database": parameters.get("database", "all"),
            "max_results": parameters.get("max_results", 5),
            "years_back": parameters.get("years_back", 5),
            "study_type": parameters.get("study_type"),
        }

    if capability in {"regulatory", "check_regulatory"}:
        return "check_regulatory", {
            "query": parameters.get("query") or query,
            "authority": parameters.get("authority"),
            "country": parameters.get("country", "br"),
        }

    if capability in {"summarize", "summarize_document"}:
        return "summarize_document", {
            "text": parameters.get("text"),
            "url": parameters.get("url"),
            "summary_type": parameters.get("summary_type", "clinical_action"),
            "max_length": parameters.get("max_length", 600),
        }

    if capability in {"translate", "translate_to_portuguese"}:
        return "translate_to_portuguese", {
            "text": parameters.get("text") or query,
            "target_style": parameters.get("target_style", "medical_ptbr"),
        }

    if capability in {"analyze_text", "analysis"}:
        return "analyze_text", {
            "text": parameters.get("text") or query,
            "instruction": parameters.get("instruction", "Analise clinica estruturada."),
            "output_format": parameters.get("output_format", "structured"),
        }

    return "web_search", {
        "query": parameters.get("query") or query,
        "focus": parameters.get("focus", "guidelines"),
        "max_results": parameters.get("max_results", 5),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    global _mcp_server, _config

    # Multi-tenancy
    from intellicare_core.tenant.startup import init_tenant_resolver
    init_tenant_resolver()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    _config = PierreConfig.from_env()
    _mcp_server = PierreMCPServer(_config)
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


# Auth integration (opcional)
try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False

app = FastAPI(
    title="intellicare-pierre",
    description="MCP Server de inteligencia externa do IntelliCare (PIERRE)",
    version=__version__,
    lifespan=lifespan,
)

# Prometheus metrics
from intellicare_core.monitoring.metrics import setup_metrics  # noqa: E402
setup_metrics(app, module_name="pierre")

if _HAS_AUTH:
    configure_auth(app, secrets_path="keycloak_client_secrets.json")

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
        "module": "intellicare-pierre",
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


@app.post("/api/v1/analyze")
async def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    """Endpoint BaseAgent para uso padrao via Wanda."""
    if _mcp_server is None:
        return {
            "success": False,
            "patient_id": request.patient_id,
            "analysis": {"error": "Server nao inicializado"},
            "recommendations": [],
            "alerts": [],
            "confidence": 0.0,
            "source": "intellicare-pierre",
        }

    parameters = request.parameters or {}
    tool_name, tool_args = _resolve_tool_payload(request.query, parameters)
    try:
        result = await _mcp_server._route_tool(tool_name, tool_args)
        confidence = 0.85 if not result.get("error") else 0.25
        return {
            "success": True,
            "patient_id": request.patient_id,
            "analysis": {
                "query": request.query,
                "capability": parameters.get("capability", "web_search"),
                "tool_used": tool_name,
                "tool_arguments": tool_args,
                "result": result,
            },
            "recommendations": [],
            "alerts": [],
            "confidence": confidence,
            "source": "intellicare-pierre",
        }
    except Exception as exc:  # pragma: no cover - fallback defensivo
        logger.error("analyze falhou: %s", exc)
        return {
            "success": False,
            "patient_id": request.patient_id,
            "analysis": {"error": str(exc), "tool_used": tool_name},
            "recommendations": [],
            "alerts": [],
            "confidence": 0.0,
            "source": "intellicare-pierre",
        }


# ──────────────────────────────────────
# Rate limiter status
# ──────────────────────────────────────

@app.get("/api/v1/rate-limit")
async def rate_limit_status() -> dict[str, Any]:
    """Status do rate limiter Tavily."""
    if _mcp_server is None:
        return {"error": "Server nao inicializado"}
    return await _mcp_server._rate_limiter.get_status()
