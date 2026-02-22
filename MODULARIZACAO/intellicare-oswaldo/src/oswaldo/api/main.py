"""
FastAPI application for Oswaldo module.

Módulo de monitoramento de doenças crônicas.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Oswaldo - Doenças Crônicas",
    version="1.0.0-dev",
    description="Motor genérico de monitoramento de doenças crônicas do IntelliCare",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================================================
# Root Endpoints
# ========================================================================
@app.get("/", tags=["root"])
def read_root():
    """Root endpoint."""
    return {
        "app": "Oswaldo",
        "status": "UP",
        "version": "1.0.0-dev",
        "description": "Motor de monitoramento de doenças crônicas"
    }


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "oswaldo"
    }


@app.get("/metrics", tags=["metrics"])
def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api", tags=["info"])
def api_info():
    """API information endpoint."""
    return {
        "name": "Oswaldo API",
        "version": "1.0.0-dev",
        "endpoints": {
            "condicoes": "/api/v1/oswaldo/condicoes",
            "acompanhamentos": "/api/v1/oswaldo/acompanhamentos",
            "alertas": "/api/v1/oswaldo/alertas",
            "docs": "/api/docs",
            "redoc": "/api/redoc"
        }
    }


# ========================================================================
# Error Handlers
# ========================================================================
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"error": "Erro de validação", "detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle generic exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Erro interno do servidor"}
    )


# ========================================================================
# Routers
# ========================================================================
from src.oswaldo.api.endpoints import condicoes_router, acompanhamentos_router, alertas_router

app.include_router(condicoes_router, prefix="/api/v1/oswaldo", tags=["condicoes"])
app.include_router(acompanhamentos_router, prefix="/api/v1/oswaldo", tags=["acompanhamentos"])
app.include_router(alertas_router, prefix="/api/v1/oswaldo", tags=["alertas"])


# ========================================================================
# Startup/Shutdown Events
# ========================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources on startup."""
    logger.info("Oswaldo API iniciando...")
    try:
        from src.oswaldo.database.session import init_db
        init_db()
        logger.info("✓ Banco de dados inicializado")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Oswaldo API encerrando...")


if __name__ == "__main__":
    import uvicorn
    
    PORT = int(os.getenv("OSWALDO_PORT", "8002"))
    HOST = os.getenv("OSWALDO_HOST", "0.0.0.0")
    
    logger.info(f"Iniciando Oswaldo em {HOST}:{PORT}")
    
    # Use import string for reload to work
    uvicorn.run(
        "src.oswaldo.api.main:app",
        host=HOST,
        port=PORT,
        reload=True  # Always reload for demo
    )
