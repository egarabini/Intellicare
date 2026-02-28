"""
FastAPI application factory for intellicare-donabedian.

Creates and configures the FastAPI app with all routes, middleware, and settings.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

# Integração intellicare-auth (Keycloak)
try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from donabedian.config import settings
from donabedian.api.middleware import RequestLoggingMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info(f"Starting {settings.module_name} v{settings.module_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database schema: {settings.database_schema}")

    # Log Keycloak authentication status
    try:
        from intellicare_auth import KeycloakConfig
        keycloak_config = KeycloakConfig()
        logger.info(f"🔐 Keycloak authentication enabled")
        logger.info(f"   Realm: {keycloak_config.realm}")
        logger.info(f"   Client: {keycloak_config.client_id}")
        logger.info(f"   Server: {keycloak_config.server_url}")
    except Exception as e:
        logger.warning(f"⚠️  Keycloak authentication not configured: {e}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.module_name}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="IntelliCare Donabedian",
        description="Módulo de avaliação de qualidade baseado no framework de Donabedian",
        version=settings.module_version,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Configurar autenticação Keycloak se disponível
    if _HAS_AUTH:
        configure_auth(app, secrets_path="keycloak_client_secrets.json")
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Register routes
    from donabedian.api.routes import health, pillars, indicators, indicator_pillars, measurements, assessment, dashboard, trends

    app.include_router(health.router, prefix="/api/v1", tags=["Health & Info"])
    app.include_router(pillars.router, prefix="/api/v1", tags=["Pillars"])
    app.include_router(indicators.router, prefix="/api/v1", tags=["Indicators"])
    app.include_router(indicator_pillars.router, prefix="/api/v1", tags=["Indicator-Pillars"])
    app.include_router(measurements.router, prefix="/api/v1", tags=["Measurements"])
    app.include_router(assessment.router, prefix="/api/v1", tags=["Quality Assessment"])
    app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
    app.include_router(trends.router, prefix="/api/v1", tags=["Trends"])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Handle all unhandled exceptions."""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={
                "method": request.method,
                "path": request.url.path,
            }
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
            }
        )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "donabedian.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level="info",
    )

