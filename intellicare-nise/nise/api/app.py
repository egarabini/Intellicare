"""FastAPI application for intellicare-nise — NISE Training & Chatbot Module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from nise.api.endpoints import oswaldo, chatbot, workflows, framingham
from nise.config import settings

# ── Logging setup ──────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ── App setup ──────────────────────────────────────────────────────

app = FastAPI(
    title="IntelliCare NISE",
    description="Núcleo de Inteligência em Saúde e Educação — Treinamento Assistido e Chatbot",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────

app.include_router(oswaldo.router, prefix="/api/v1")
app.include_router(chatbot.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(framingham.router, prefix="/api/v1")

# ── Health & Info endpoints ────────────────────────────────────────


@app.get("/health")
@app.get("/api/v1/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "intellicare-nise",
        "version": "1.0.0"
    }


@app.get("/api/v1/info")
async def info():
    """Module info endpoint."""
    return {
        "name": "intellicare-nise",
        "version": "1.0.0",
        "capabilities": [
            "oswaldo-integration",
            "chatbot",
            "rag",
            "flowise",
            "ollama",
            "kestra-workflows"
        ],
        "description": "Núcleo de Inteligência em Saúde e Educação",
        "metadata": {
            "integrations": ["oswaldo", "florence", "flowise", "ollama", "kestra"],
            "endpoints": [
                "/api/v1/oswaldo/paciente/{id}/resumo",
                "/api/v1/oswaldo/paciente/{id}/diagnosticos",
                "/api/v1/oswaldo/paciente/{id}/alertas",
                "/api/v1/chatbot/chat",
                "/api/v1/workflows/trigger",
                "/api/v1/workflows/executions"
            ]
        }
    }


# ── Startup & Shutdown ─────────────────────────────────────────────


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("🚀 IntelliCare NISE starting up...")
    logger.info("✅ NISE API ready on port 8000")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("👋 IntelliCare NISE shutting down...")


# ── Main ───────────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "nise.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )

