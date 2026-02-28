"""
Analytics Data Access for donabedian module.

Provides read-only access to donabedian_analitico schema.
Implements BI-focused queries and rejects all writes.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .base import BaseDAO, T

logger = logging.getLogger(__name__)


class AnalyticsDataAccess(BaseDAO):
    """
    Analytics data access - read-only from donabedian_analitico schema.
    
    Enforces:
    - Read-only access to *_analitico
    - Rejects CREATE/UPDATE/DELETE with PermissionError
    - BI-focused queries (aggregations, denormalized views)
    - Consolidation metadata (consolidated_at, consolidation_source)
    """

    def create(self, entity: T) -> T:
        """
        Reject CREATE on analytics schema.
        
        Raises:
            PermissionError: Analytics schema is read-only
        """
        raise PermissionError(
            f"Cannot CREATE in analytics schema. "
            f"Use OperationalDataAccess for write operations."
        )

    def update(self, entity: T) -> T:
        """
        Reject UPDATE on analytics schema.
        
        Raises:
            PermissionError: Analytics schema is read-only
        """
        raise PermissionError(
            f"Cannot UPDATE in analytics schema. "
            f"Use OperationalDataAccess for write operations."
        )

    def delete(self, entity_id: UUID) -> bool:
        """
        Reject DELETE on analytics schema.
        
        Raises:
            PermissionError: Analytics schema is read-only
        """
        raise PermissionError(
            f"Cannot DELETE in analytics schema. "
            f"Use OperationalDataAccess for write operations."
        )

    def read(self, entity_id: UUID) -> Optional[T]:
        """
        Read entity from donabedian_analitico.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            Entity or None if not found
        """
        return self.session.query(self.entity_class).filter(
            self.entity_class.id == entity_id
        ).first()

    def list(self, limit: int = 100, offset: int = 0) -> list[T]:
        """
        List entities from donabedian_analitico.
        
        Args:
            limit: Max records
            offset: Skip records
            
        Returns:
            List of entities
        """
        return self.session.query(self.entity_class).limit(limit).offset(offset).all()

    def read_all_denormalized(self, filters: Optional[Dict[str, Any]] = None) -> list[T]:
        """
        Read all records with optional filters (analytics query).
        
        Args:
            filters: Dictionary of column=value for WHERE clause
            
        Returns:
            List of entities matching filters
        """
        query = self.session.query(self.entity_class)

        if filters:
            for column_name, value in filters.items():
                if hasattr(self.entity_class, column_name):
                    column = getattr(self.entity_class, column_name)
                    query = query.filter(column == value)

        return query.all()

    def aggregate(self, aggregation: str, column_name: str) -> Optional[Any]:
        """
        Perform aggregation on column (SUM, AVG, MAX, MIN, COUNT).
        
        Args:
            aggregation: Type of aggregation (SUM, AVG, MAX, MIN, COUNT)
            column_name: Column to aggregate
            
        Returns:
            Aggregated value
        """
        if not hasattr(self.entity_class, column_name):
            raise ValueError(f"Column {column_name} not found on {self.entity_class.__name__}")

        column = getattr(self.entity_class, column_name)

        agg_func = {
            "SUM": func.sum,
            "AVG": func.avg,
            "MAX": func.max,
            "MIN": func.min,
            "COUNT": func.count,
        }.get(aggregation.upper())

        if not agg_func:
            raise ValueError(f"Unknown aggregation: {aggregation}")

        return self.session.query(agg_func(column)).scalar()

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching optional filters.
        
        Args:
            filters: Dictionary of column=value for WHERE clause
            
        Returns:
            Number of matching records
        """
        query = self.session.query(func.count(self.entity_class.id))

        if filters:
            for column_name, value in filters.items():
                if hasattr(self.entity_class, column_name):
                    column = getattr(self.entity_class, column_name)
                    query = query.filter(column == value)

        return query.scalar() or 0

    def get_statistics(self, column_name: str) -> Dict[str, Any]:
        """
        Get statistics (count, sum, avg, max, min) for a numeric column.
        
        Args:
            column_name: Column to analyze
            
        Returns:
            Dict with count, sum, avg, max, min
        """
        if not hasattr(self.entity_class, column_name):
            raise ValueError(f"Column {column_name} not found")

        column = getattr(self.entity_class, column_name)

        result = self.session.query(
            func.count(column).label("count"),
            func.sum(column).label("sum"),
            func.avg(column).label("avg"),
            func.max(column).label("max"),
            func.min(column).label("min"),
        ).first()

        if not result:
            return {
                "count": 0,
                "sum": None,
                "avg": None,
                "max": None,
                "min": None,
            }

        return {
            "count": result.count,
            "sum": result.sum,
            "avg": result.avg,
            "max": result.max,
            "min": result.min,
        }
