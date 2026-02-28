"""Data Access layer — DAO patterns para operacional vs analítico."""

from .base import BaseDAO
from .operational import OperationalDataAccess
from .analytics import AnalyticsDataAccess

__all__ = [
    "BaseDAO",
    "OperationalDataAccess",
    "AnalyticsDataAccess",
]
