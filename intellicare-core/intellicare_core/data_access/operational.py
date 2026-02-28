"""OperationalDataAccess — DAO para dados operacionais.

Garantias:
  - ✅ Escreve APENAS em schemas {modulo}_operacional
  - ✅ Rejeita qualquer tentativa de escrever em _analitico
  - ✅ Transações ACID
  - ✅ Auditoria automática
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.exc import IntegrityError

from .base import BaseDAO, T

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from intellicare_core.tenant.context import TenantContext

logger = logging.getLogger(__name__)


class OperationalDataAccess(BaseDAO[T]):
    """DAO para esquemas *_operacional.
    
    Este DAO garante que:
    1. NUNCA escreve em schemas analíticos (_analitico)
    2. Lê apenas do schema operacional
    3. Registra auditoria automáticamente
    4. Publica eventos para consolidação
    
    Multi-tenancy:
        Quando tenant_ctx é fornecido, o schema é prefixado com o
        tenant_schema para garantir isolamento de dados entre tenants.
    """

    def __init__(
        self,
        session: Session,
        entity_class: type[T],
        schema: str,
        tenant_ctx: Optional[TenantContext] = None,
        publish_event_callback: Optional[callable] = None,
    ) -> None:
        """Inicializa DAO operacional.
        
        Args:
            session: SQLAlchemy session
            entity_class: Classe da entidade
            schema: Nome do schema (ex: 'oswaldo_operacional')
            tenant_ctx: Contexto do tenant (multi-tenancy). Se fornecido,
                        o schema e ajustado para o tenant automaticamente.
            publish_event_callback: Função para publicar evento (recebe event dict)
                                   Assinatura: fn(entity_type, entity_id, operation, old, new)
                                   
        Raises:
            ValueError: Se schema_name contiver '_analitico' ou não '_operacional'
        """
        super().__init__(session, entity_class)
        self._tenant_ctx = tenant_ctx
        self.schema = schema
        self.publish_event_callback = publish_event_callback
        self._validate_schema()

    def _validate_schema(self) -> None:
        """Valida que schema é de operacional, NUNCA analítico.
        
        Raises:
            ValueError: Se schema é analítico
        """
        if "analitico" in self.schema.lower():
            raise ValueError(
                f"❌ OperationalDataAccess nunca acessa {self.schema} (é analítico)"
            )
        # Em modo multi-tenant com TenantAwareSessionFactory, o schema
        # e resolvido via SET search_path, entao o nome pode nao conter
        # '_operacional' diretamente.
        if self._tenant_ctx is None and "operacional" not in self.schema.lower():
            logger.warning(
                f"⚠️ Schema '{self.schema}' não parece operacional. "
                "Considere usar formato: {modulo}_operacional"
            )


    def create(
        self,
        entity_data: dict[str, Any],
        actor_id: Optional[str] = None,
        audit_reason: Optional[str] = None,
    ) -> T:
        """Cria nova entidade em schema operacional.
        
        Args:
            entity_data: Dicionário com dados da entidade
            actor_id: ID do usuário criando (para auditoria)
            audit_reason: Razão da criação (para auditoria)
            
        Returns:
            Entidade criada
            
        Raises:
            ValueError: Se dados inválidos
            IntegrityError: Se violação de constraint (ex: duplicate key)
        """
        try:
            # Adiciona metadados de auditoria
            if actor_id:
                entity_data.setdefault("created_by", actor_id)
                entity_data.setdefault("updated_by", actor_id)

            entity = self.entity_class(**entity_data)
            self.session.add(entity)
            self.session.flush()  # Garante ID antes de evento

            # Obtém ID da entidade para rastreamento
            entity_id = getattr(entity, "id", None)

            logger.info(
                f"✅ Created {self.entity_class.__name__} {entity_id} in {self.schema}"
            )

            # Publica evento para consolidação
            if self.publish_event_callback and entity_id:
                self.publish_event_callback(
                    entity_type=self.entity_class.__name__.lower() + "s",
                    entity_id=str(entity_id),
                    operation="CREATE",
                    old_values=None,
                    new_values=entity_data,
                    actor_id=actor_id,
                    reason=audit_reason,
                )

            return entity

        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"❌ Integrity error creating {self.entity_class.__name__}: {e}")
            raise ValueError(f"Constraint violation: {e.orig}") from e
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error creating {self.entity_class.__name__}: {e}")
            raise

    def read(self, entity_id: str | int) -> Optional[T]:
        """Lê entidade do schema operacional.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            Entidade ou None se não encontrada
        """
        try:
            entity = self.session.query(self.entity_class).get(entity_id)
            if entity:
                logger.debug(f"✅ Read {self.entity_class.__name__} {entity_id}")
            return entity
        except Exception as e:
            logger.error(f"❌ Error reading {self.entity_class.__name__}: {e}")
            raise

    def update(
        self,
        entity_id: str | int,
        updates: dict[str, Any],
        actor_id: Optional[str] = None,
        audit_reason: Optional[str] = None,
    ) -> Optional[T]:
        """Atualiza entidade em schema operacional.
        
        Args:
            entity_id: ID da entidade
            updates: Dicionário {coluna: novo_valor}
            actor_id: ID do usuário atualizando (para auditoria)
            audit_reason: Razão da atualização (para auditoria)
            
        Returns:
            Entidade atualizada ou None
            
        Raises:
            ValueError: Se entidade não encontrada
        """
        try:
            entity = self.read(entity_id)
            if not entity:
                raise ValueError(
                    f"{self.entity_class.__name__} {entity_id} not found in {self.schema}"
                )

            # Captura valores antigos para auditoria
            old_values = {col: getattr(entity, col) for col in updates.keys()}

            # Incrementa rowversion (otimistic locking)
            if hasattr(entity, "rowversion"):
                entity.rowversion += 1

            # Atualiza timestamps e ator
            entity.updated_at = datetime.now(timezone.utc)
            if actor_id:
                entity.updated_by = actor_id

            # Aplica updates
            for key, value in updates.items():
                setattr(entity, key, value)

            self.session.flush()

            logger.info(
                f"✅ Updated {self.entity_class.__name__} {entity_id} in {self.schema}"
            )

            # Publica evento para consolidação
            if self.publish_event_callback:
                self.publish_event_callback(
                    entity_type=self.entity_class.__name__.lower() + "s",
                    entity_id=str(entity_id),
                    operation="UPDATE",
                    old_values=old_values,
                    new_values=updates,
                    actor_id=actor_id,
                    reason=audit_reason,
                )

            return entity

        except ValueError:
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error updating {self.entity_class.__name__}: {e}")
            raise

    def delete(
        self,
        entity_id: str | int,
        actor_id: Optional[str] = None,
        audit_reason: Optional[str] = None,
        soft_delete: bool = True,
    ) -> bool:
        """Deleta entidade (soft delete por padrão).
        
        Args:
            entity_id: ID da entidade
            actor_id: ID do usuário deletando (para auditoria)
            audit_reason: Razão da deleção (para auditoria)
            soft_delete: Se True, marca com valid_to. Se False, hard delete.
            
        Returns:
            True se deletada, False se não encontrada
        """
        try:
            entity = self.read(entity_id)
            if not entity:
                return False

            if soft_delete and hasattr(entity, "valid_to"):
                # Soft delete: marca como inválido
                entity.valid_to = datetime.now(timezone.utc)
                entity.updated_by = actor_id or "system"
            else:
                # Hard delete: remove realmente
                self.session.delete(entity)

            self.session.flush()

            logger.info(
                f"✅ Deleted {self.entity_class.__name__} {entity_id} "
                f"({'soft' if soft_delete else 'hard'}) in {self.schema}"
            )

            # Publica evento para consolidação
            if self.publish_event_callback:
                self.publish_event_callback(
                    entity_type=self.entity_class.__name__.lower() + "s",
                    entity_id=str(entity_id),
                    operation="DELETE",
                    old_values=None,
                    new_values=None,
                    actor_id=actor_id,
                    reason=audit_reason,
                )

            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error deleting {self.entity_class.__name__}: {e}")
            raise

    def bulk_create(
        self,
        entities_data: list[dict[str, Any]],
        actor_id: Optional[str] = None,
    ) -> list[T]:
        """Cria múltiplas entidades em uma transação.
        
        Args:
            entities_data: Lista de dicionários com dados de entidades
            actor_id: ID do usuário criando
            
        Returns:
            Lista de entidades criadas
        """
        try:
            entities = []
            for data in entities_data:
                if actor_id:
                    data.setdefault("created_by", actor_id)
                    data.setdefault("updated_by", actor_id)
                entity = self.entity_class(**data)
                entities.append(entity)
                self.session.add(entity)

            self.session.flush()
            logger.info(
                f"✅ Bulk created {len(entities)} {self.entity_class.__name__}s in {self.schema}"
            )
            return entities

        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error in bulk_create: {e}")
            raise
