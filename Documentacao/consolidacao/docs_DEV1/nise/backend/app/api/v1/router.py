"""
============================================================================
NISE TRAINING MODULE - API V1 ROUTER
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: API V1 Router
Versão: 1.0
Data: 17/03/2026
Responsável: DEV2
============================================================================
"""

from fastapi import APIRouter
from app.api.v1.endpoints import patients, observations, practitioners, encounters, florence

# ============================================================================
# API V1 ROUTER
# ============================================================================

api_router = APIRouter(prefix="/api/v1")

# Register FHIR endpoints
api_router.include_router(patients.router)
api_router.include_router(observations.router)
api_router.include_router(practitioners.router)
api_router.include_router(encounters.router)

# Register Florence AI Assistant
api_router.include_router(florence.router)

