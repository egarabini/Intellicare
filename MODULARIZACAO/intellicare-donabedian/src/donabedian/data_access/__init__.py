"""
Data Access Layer for donabedian module.

Provides generic DAO pattern with separation between operational and analytical access.
"""

from .base import BaseDAO
from .operational import OperationalDataAccess
from .analytics import AnalyticsDataAccess

__all__ = [
    "BaseDAO",
    "OperationalDataAccess",
    "AnalyticsDataAccess",
]
