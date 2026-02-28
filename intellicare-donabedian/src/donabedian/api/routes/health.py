"""
Health check and info endpoints.

Provides endpoints for monitoring service health and retrieving module information.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.config import settings
from donabedian.api.dependencies import get_db
from donabedian.schemas.common import HealthResponse, InfoResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.
    
    Verifies that the service is running and can connect to the database.
    
    Args:
        db: Database session
        
    Returns:
        HealthResponse: Service health status
    """
    # Test database connection
    try:
        await db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        database_status = "disconnected"
    
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

