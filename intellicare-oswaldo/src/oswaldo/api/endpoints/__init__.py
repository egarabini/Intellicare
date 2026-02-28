"""
API endpoints package para Oswaldo.
"""

from src.oswaldo.api.endpoints.condicoes import router as condicoes_router
from src.oswaldo.api.endpoints.acompanhamentos import router as acompanhamentos_router
from src.oswaldo.api.endpoints.alertas import router as alertas_router

__all__ = [
    "condicoes_router",
    "acompanhamentos_router",
    "alertas_router",
]
