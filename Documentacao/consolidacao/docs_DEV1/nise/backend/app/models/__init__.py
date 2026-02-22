"""
============================================================================
NISE TRAINING MODULE - MODELS PACKAGE
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: SQLAlchemy Models
Versão: 1.0
Data: 17/03/2026
Responsável: DEV2
============================================================================
"""

from app.models.patient import Patient
from app.models.observation import Observation
from app.models.practitioner import Practitioner
from app.models.encounter import Encounter

__all__ = [
    "Patient",
    "Observation",
    "Practitioner",
    "Encounter"
]

