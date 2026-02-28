"""FastAPI application for intellicare-wanda — Intelligent Orchestrator (v3.0)."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import FastAPI, Query

# Integração intellicare-auth (Keycloak)
try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False
from pydantic import BaseModel

from wanda.config import WandaConfig
from wanda.orchestrator.orchestrator import WandaOrchestrator

# v2.0 routers (EF-W001, EF-W002, EF-W011)
from wanda.api.registry_routes import router as registry_router, init_registry_routes
from wanda.api.ips_routes import router as ips_router, init_ips_routes
from wanda.api.mcp_routes import router as mcp_router, init_mcp_routes
# v2.1 routers (EF-W003, EF-W004)
from wanda.api.routing_routes import router as routing_router, init_routing_routes
from wanda.api.aggregation_routes import router as aggregation_router, init_aggregation_routes
from wanda.api.resilience_routes import router as resilience_router, init_resilience_routes
from wanda.api.trace_routes import router as trace_router, init_trace_routes
from wanda.api.metrics_routes import router as metrics_router, init_metrics_routes
# v3.0 routers (EF-W005/W006/W007/W012/W013)
from wanda.api.workflow_routes import router as workflow_router
from wanda.api.alert_routes import router as alert_router
from wanda.api.event_routes import router as event_router
from wanda.api.bot_routes import router as bot_router
from wanda.api.nise_routes import router as nise_router

logger = logging.getLogger(__name__)

# ── App setup ──────────────────────────────────────────────────

config = WandaConfig()
orchestrator = WandaOrchestrator(config=config)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: initialize v2.0 subsystems. Shutdown: cleanup."""
    # Initialize registry routes with the orchestrator's registry
    init_registry_routes(
        registry=getattr(orchestrator, "persistent_registry", None),
        discovery=getattr(orchestrator, "discovery_service", None),
    )

    # Initialize IPS routes
    ips_manager = getattr(orchestrator, "ips_manager", None)
    ips_enricher = getattr(orchestrator, "ips_enricher", None)
    if ips_manager:
        init_ips_routes(ips_manager, ips_enricher)

    # Initialize MCP routes
    mcp_client = getattr(orchestrator, "mcp_client", None)
    tool_registry = getattr(orchestrator, "tool_registry", None)
    if mcp_client:
        init_mcp_routes(mcp_client, tool_registry)

    # Initialize routing routes (EF-W003)
    intent_router = getattr(orchestrator, "intent_router", None)
    init_routing_routes(
        intent_router=intent_router,
        keyword_router=orchestrator.router,
        registry=orchestrator.registry,
        routing_method="llm" if intent_router else "keyword",
    )

    # Initialize aggregation routes (EF-W004)
    intelligent_aggregator = getattr(orchestrator, "intelligent_aggregator", None)
    init_aggregation_routes(
        intelligent_aggregator=intelligent_aggregator,
        simple_aggregator=orchestrator.aggregator,
    )

    # Initialize resilience/observability routes (EF-W008/009/010)
    init_resilience_routes(
        health_dashboard=getattr(orchestrator, "health_dashboard", None),
        circuit_breaker_manager=getattr(orchestrator, "circuit_breaker_manager", None),
    )
    init_trace_routes(
        trace_store=getattr(orchestrator, "trace_store", None),
    )
    init_metrics_routes(
        metrics_registry=getattr(orchestrator, "metrics_registry", None),
    )

    # ── v3.0: Register state objects for route access ─────────────
    app.state.workflow_executor = getattr(orchestrator, "workflow_executor", None)
    app.state.alert_hub = getattr(orchestrator, "alert_hub", None)
    app.state.event_consumer = getattr(orchestrator, "event_consumer", None)
    app.state.event_coordinator = getattr(orchestrator, "event_coordinator", None)
    app.state.bot_handler = getattr(orchestrator, "bot_handler", None)
    app.state.nise_gateway = getattr(orchestrator, "nise_gateway", None)
    app.state.metrics_registry = getattr(orchestrator, "metrics_registry", None)

    # ── v3.0: Start background tasks ──────────────────────────────
    alert_hub = app.state.alert_hub
    if alert_hub is not None:
        await alert_hub.start()

    event_consumer = app.state.event_consumer
    if event_consumer is not None:
        await event_consumer.start_consuming()

    logger.info(
        "Wanda v%s started (persistence=%s, redis=%s, mcp=%s, ollama=%s, langgraph=%s, alerts=%s, bot=%s, nise=%s)",
        config.module_version,
        config.enable_persistence,
        config.enable_redis,
        config.enable_mcp,
        config.enable_ollama,
        config.enable_langgraph,
        config.enable_alert_hub,
        config.enable_rc_bot,
        config.enable_dr_nise,
    )

    yield  # Application runs here

    # ── Shutdown ───────────────────────────────────────────────────
    if event_consumer is not None:
        await event_consumer.stop_consuming()
    if alert_hub is not None:
        await alert_hub.stop()

    logger.info("Wanda shutting down")



app = FastAPI(
    title="IntelliCare Wanda",
    description="Orquestrador inteligente — coordena modulos IntelliCare via HTTP + MCP",
    version=config.module_version,
    lifespan=lifespan,
)

# Configurar autenticação Keycloak se disponível
if _HAS_AUTH:
    configure_auth(app, secrets_path="keycloak_client_secrets.json")

# Include v2.0 routers
app.include_router(registry_router)
app.include_router(ips_router)
app.include_router(mcp_router)
# Include v2.1 routers
app.include_router(routing_router)
app.include_router(aggregation_router)
app.include_router(resilience_router)
app.include_router(trace_router)
app.include_router(metrics_router)
# Include v3.0 routers
app.include_router(workflow_router)
app.include_router(alert_router)
app.include_router(event_router)
app.include_router(bot_router)
app.include_router(nise_router)


# ── Request models ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    patient_id: Optional[str] = None
    session_id: Optional[str] = None


# ── Contract endpoints ─────────────────────────────────────────

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "module_name": config.module_name,
        "version": config.module_version,
        "modules_online": orchestrator.registry.online_count,
    }


@app.get("/api/v1/info")
async def info():
    return {
        "name": config.module_name,
        "version": config.module_version,
        "description": "Orquestrador inteligente — Wanda de Aguiar Horta",
        "capabilities": [
            "orchestration",
            "multi-agent",
            "module-discovery",
            "safety-rules",
            "ips-first",
        ],
    }


# ── Orchestration endpoints ───────────────────────────────────

@app.post("/api/v1/chat")
async def chat(req: ChatRequest):
    result = await orchestrator.chat(
        message=req.message,
        patient_id=req.patient_id,
        session_id=req.session_id,
    )
    return {
        "success": True,
        "data": {
            "response": result.aggregated_response,
            "modules_used": result.modules_used,
            "safety_warnings": result.safety_warnings,
            "routing": result.routing_decision.to_dict() if result.routing_decision else None,
        },
    }


@app.post("/api/v1/route")
async def route_query(req: ChatRequest):
    """Preview which modules would handle a query (without calling them)."""
    if not orchestrator._discovered:
        await orchestrator.discover_modules()

    online = orchestrator.registry.get_online_modules()
    routing = orchestrator.router.route(
        query=req.message,
        available_modules=online,
        patient_id=req.patient_id,
    )
    return {
        "success": True,
        "data": routing.to_dict(),
    }


# ── Module management endpoints ───────────────────────────────

@app.get("/api/v1/modules")
async def list_modules():
    status = await orchestrator.get_module_status()
    return {"success": True, "data": status}


@app.post("/api/v1/modules/discover")
async def discover():
    """Force re-discovery of all modules."""
    count = await orchestrator.discover_modules()
    status = await orchestrator.get_module_status()
    return {
        "success": True,
        "data": status,
        "online_count": count,
    }


@app.get("/api/v1/modules/{module_name}")
async def get_module(module_name: str):
    module = orchestrator.registry.get_module(module_name)
    if not module:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Modulo nao encontrado")
    return {"success": True, "data": module.to_dict()}


@app.get("/api/v1/capabilities")
async def list_capabilities(capability: Optional[str] = Query(None)):
    """List modules by capability."""
    if not orchestrator._discovered:
        await orchestrator.discover_modules()

    if capability:
        modules = orchestrator.registry.get_modules_with_capability(capability)
    else:
        modules = orchestrator.registry.get_online_modules()

    return {
        "success": True,
        "data": [m.to_dict() for m in modules],
        "total": len(modules),
    }
