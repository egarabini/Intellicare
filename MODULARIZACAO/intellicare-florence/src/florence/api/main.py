"""
Florence API Main Application
=============================

FastAPI application para validação clínica e anonimização de dados.

Uso:
    python -m uvicorn src.florence.api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path - absolute path to src directory
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import routers directly from file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "validacao",
    os.path.join(os.path.dirname(__file__), 'endpoints/validacao.py')
)
validacao = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validacao)

# Create FastAPI app
app = FastAPI(
    title="Florence API",
    description="API para validação clínica e anonimização de dados - IntelliCare",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(validacao.router)


@app.get("/", tags=["status"])
def root():
    """Root endpoint - check if API is running"""
    return {
        "application": "Florence API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/api/docs",
        "endpoints": {
            "health_check": "/api/v1/validacao/saude",
            "tipos_suportados": "/api/v1/validacao/tipos-suportados",
            "validar_exame": "/api/v1/validacao/validador-clinico"
        }
    }


@app.get("/health", tags=["status"])
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "application": "Florence"
    }


@app.get("/api", tags=["status"])
def api_root():
    """API root endpoint"""
    return {
        "application": "Florence API v1.0.0",
        "endpoints": {
            "validacao": "/api/v1/validacao",
            "swagger": "/api/docs",
            "redoc": "/api/redoc"
        }
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
