"""
Health check and info endpoints.

Provides endpoints for monitoring service health and retrieving module information.
"""

from fastapi import APIRouter
from sqlalchemy import text

from donabedian.config import settings
from donabedian.schemas.common import HealthResponse, InfoResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint — público, sem autenticação.

    Verifica se o serviço está rodando e se consegue conectar ao banco.
    Não requer JWT nem tenant context para que o Docker healthcheck funcione.
    """
    from donabedian.database.session import AsyncSessionLocal

    database_status = "disconnected"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            database_status = "connected"
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if database_status == "connected" else "unhealthy",
        module=settings.module_name,
        version=settings.module_version,
        database=database_status,
    )


@router.get("/info", response_model=InfoResponse)
async def module_info() -> InfoResponse:
    """
    Module information endpoint.
    
    Returns detailed information about the module including name, version,
    description, and configuration.
    
    Returns:
        InfoResponse: Module information
    """
    return InfoResponse(
        name=settings.module_name,
        version=settings.module_version,
        description="Módulo de avaliação de qualidade baseado no framework de Donabedian",
        environment=settings.environment,
        database_schema=settings.database_schema,
        api_version="v1",
    )

