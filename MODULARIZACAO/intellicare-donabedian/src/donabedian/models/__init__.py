"""
SQLAlchemy models for intellicare-donabedian.

Models:
- Pillar: 7 pilares de Donabedian (tabela de referência)
- Indicator: Indicadores de qualidade
- IndicatorPillar: Tabela associativa N:N com weight
- Measurement: Medições temporais dos indicadores
"""

from sqlalchemy.orm import DeclarativeBase
from donabedian.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Define schema for all tables in this module
    # If schema is None (e.g., for SQLite tests), don't set it
    __table_args__ = {"schema": settings.db_schema} if settings.db_schema else {}


# Import models to register them with Base
from donabedian.models.pillar import Pillar  # noqa: E402, F401
from donabedian.models.indicator import Indicator  # noqa: E402, F401
from donabedian.models.indicator_pillar import IndicatorPillar  # noqa: E402, F401
from donabedian.models.measurement import Measurement  # noqa: E402, F401


__all__ = [
    "Base",
    "Pillar",
    "Indicator",
    "IndicatorPillar",
    "Measurement",
]
