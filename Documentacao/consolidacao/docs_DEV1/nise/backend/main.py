"""
============================================================================
NISE TRAINING MODULE - MAIN APPLICATION
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: FastAPI Main Application
Versão: 1.0
Data: 04/03/2026
Responsável: DEV2
============================================================================
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

# Importar routers
from app.api.v1.router import api_router
from app.api.v1.openapi import custom_openapi

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    # Startup
    logger.info("🚀 NISE Training Module - Starting up...")
    logger.info("📊 Connecting to PostgreSQL...")
    logger.info("🔌 Initializing pgvector...")
    logger.info("✅ NISE Training Module - Ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 NISE Training Module - Shutting down...")
    logger.info("📊 Closing database connections...")
    logger.info("✅ NISE Training Module - Stopped!")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="NISE - Treinamento Assistido",
    description="""
    ## 🎓 NISE Training Module

    Sistema de treinamento assistido para profissionais de saúde com:
    - 🏥 Dados sintéticos FHIR R4 (pacientes, observações, profissionais)
    - 📚 Cenários clínicos estruturados (100 cenários)
    - 🤖 Chatbot de suporte (Florence/Dr. Nise - Flowise + Ollama)
    - 📊 Avaliação automática com LLM
    - 🎯 Sistema de certificação

    **Homenagem**: Nise da Silveira - "Aprender fazendo"
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Configure custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configurar origins específicas em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Adicionar tempo de processamento no header"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log requests lentos (>100ms)
    if process_time > 0.1:
        logger.warning(
            f"⚠️ Slow request: {request.method} {request.url.path} "
            f"took {process_time:.3f}s"
        )
    
    return response

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções não tratadas"""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Health check"""
    return {
        "status": "healthy",
        "service": "NISE Training Module",
        "version": "1.0.0",
        "message": "🎓 NISE - Aprender fazendo (Nise da Silveira)"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "NISE Training Module",
        "version": "1.0.0",
        "components": {
            "api": "healthy",
            "database": "healthy",  # TODO: Verificar conexão real
            "pgvector": "healthy",  # TODO: Verificar extensão
            "flowise": "pending",   # TODO: Verificar quando integrado
            "ollama": "pending"     # TODO: Verificar quando integrado
        }
    }

# ============================================================================
# API ROUTES
# ============================================================================

# Include API v1 router
app.include_router(api_router)

# ============================================================================
# METADATA ENDPOINT
# ============================================================================

@app.get("/api/v1/metadata", tags=["Metadata"])
async def get_metadata():
    """Get FHIR server metadata (CapabilityStatement)"""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2026-03-17",
        "kind": "instance",
        "software": {
            "name": "NISE Training Module",
            "version": "1.0.0"
        },
        "implementation": {
            "description": "NISE - Treinamento Assistido com FHIR R4",
            "url": "http://localhost:8000"
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "name", "type": "string"},
                            {"name": "gender", "type": "token"},
                            {"name": "birthdate", "type": "date"},
                            {"name": "identifier", "type": "token"}
                        ]
                    },
                    {
                        "type": "Observation",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "patient", "type": "reference"},
                            {"name": "code", "type": "token"},
                            {"name": "status", "type": "token"},
                            {"name": "date", "type": "date"},
                            {"name": "category", "type": "token"}
                        ]
                    },
                    {
                        "type": "Practitioner",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "name", "type": "string"},
                            {"name": "identifier", "type": "token"},
                            {"name": "specialty", "type": "string"}
                        ]
                    },
                    {
                        "type": "Encounter",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "patient", "type": "reference"},
                            {"name": "status", "type": "token"},
                            {"name": "class", "type": "token"},
                            {"name": "date", "type": "date"}
                        ]
                    }
                ]
            }
        ]
    }

# ============================================================================
# ROUTERS (serão adicionados progressivamente)
# ============================================================================

# TODO: Adicionar routers conforme implementação
# app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])
# app.include_router(observations.router, prefix="/api/v1/observations", tags=["Observations"])
# app.include_router(practitioners.router, prefix="/api/v1/practitioners", tags=["Practitioners"])
# app.include_router(encounters.router, prefix="/api/v1/encounters", tags=["Encounters"])
# app.include_router(scenarios.router, prefix="/api/v1/scenarios", tags=["Scenarios"])
# app.include_router(training_sessions.router, prefix="/api/v1/training", tags=["Training"])

# ============================================================================
# MAIN (para desenvolvimento)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

