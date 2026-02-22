"""Base DAO — padrão genérico para acesso a dados."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseDAO(ABC, Generic[T]):
    """DAO abstrato genérico com CRUD base.
    
    Subclasses devem implementar métodos específicos de negócio.
    """

    def __init__(self, session: Session, entity_class: type[T]) -> None:
        """Inicializa DAO.
        
        Args:
            session: SQLAlchemy session
            entity_class: Classe da entidade (ex: Paciente)
        """
        self.session = session
        self.entity_class = entity_class

    @abstractmethod
    def create(self, entity_data: dict[str, Any]) -> T:
        """Cria uma nova entidade.
        
        Args:
            entity_data: Dicionário com dados da entidade
            
        Returns:
            Entidade criada
            
        Raises:
            ValueError: Se dados inválidos
            IntegrityError: Se violação de constraint
        """
        pass

    @abstractmethod
    def read(self, entity_id: str | int) -> Optional[T]:
        """Lê uma entidade por ID.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            Entidade encontrada ou None
        """
        pass

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[T]:
        """Lista entidades com filtros opcionais.
        
        Args:
            skip: Número de registros a pular (offset)
            limit: Número máximo de registros (limit 100 por padrão)
            filters: Dicionário de filtros {coluna: valor}
            
        Returns:
            Lista de entidades
        """
        from sqlalchemy import select

        query = select(self.entity_class)

        if filters:
            for key, value in filters.items():
                if hasattr(self.entity_class, key):
                    query = query.where(getattr(self.entity_class, key) == value)

        return self.session.execute(query.offset(skip).limit(limit)).scalars().all()

    @abstractmethod
    def update(self, entity_id: str | int, updates: dict[str, Any]) -> Optional[T]:
        """Atualiza uma entidade.
        
        Args:
            entity_id: ID da entidade
            updates: Dicionário {coluna: novo_valor}
            
        Returns:
            Entidade atualizada ou None se não encontrada
            
        Raises:
            ValueError: Se entidade não encontrada
        """
        pass

    @abstractmethod
    def delete(self, entity_id: str | int) -> bool:
        """Deleta uma entidade.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            True se deletada, False se não encontrada
        """
        pass
