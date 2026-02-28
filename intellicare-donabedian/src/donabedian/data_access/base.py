"""
Data Access Layer for donabedian module following FASE 1 architecture.

This module provides a generic BaseDAO for all data access operations
and implements separation between operational (transactional) and
analytical (read-only, BI-focused) databases.

Pattern: Generic DAO[T] with TypeVar
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

# Type variable for generics
T = TypeVar("T")


class BaseDAO(ABC, Generic[T]):
    """
    Abstract base class for all Data Access Objects.
    
    Provides generic CRUD operations for any entity type.
    All DAOs must inherit from this class.
    
    Type Parameter:
        T: Entity model class (e.g., Pilar, Indicator, Measurement)
    """

    def __init__(self, session: Session, entity_class: type[T]):
        """
        Initialize DAO with database session.
        
        Args:
            session: SQLAlchemy session
            entity_class: Entity class (model)
        """
        self.session = session
        self.entity_class = entity_class

    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Create new entity in database.
        
        Args:
            entity: Entity instance to create
            
        Returns:
            Created entity with ID
        """
        pass

    @abstractmethod
    def read(self, entity_id: UUID) -> Optional[T]:
        """
        Read entity by ID.
        
        Args:
            entity_id: UUID of entity
            
        Returns:
            Entity instance or None if not found
        """
        pass

    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        List entities with pagination.
        
        Args:
            limit: Maximum records to return
            offset: Number of records to skip
            
        Returns:
            List of entities
        """
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Update existing entity.
        
        Args:
            entity: Entity with updated fields
            
        Returns:
            Updated entity
        """
        pass

    @abstractmethod
    def delete(self, entity_id: UUID) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: UUID of entity to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
