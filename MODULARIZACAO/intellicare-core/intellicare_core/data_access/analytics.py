"""AnalyticsDataAccess — DAO para dados analíticos (READ-ONLY).

Garantias:
  - ✅ Lê APENAS de schemas {modulo}_analitico
  - ✅ REJEITA qualquer tentativa de escrita (CREATE, UPDATE, DELETE)
  - ✅ Otimizado para queries de BI (denormalizadas, índices)
  - ✅ Suporta agregações complexas
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from .base import BaseDAO, T

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AnalyticsDataAccess(BaseDAO[T]):
    """DAO read-only para esquemas *_analitico.
    
    Este DAO garante que:
    1. Lê APENAS de schemas analíticos (_analitico)
    2. REJEITA qualquer escrita (create, update, delete)
    3. Fornece métodos de agregação para BI
    4. Suporta queries complexas e denormalizadas
    """

    def __init__(
        self,
        session: Session,
        entity_class: type[T],
        schema: str,
    ) -> None:
        """Inicializa DAO de análise (read-only).
        
        Args:
            session: SQLAlchemy session
            entity_class: Classe da entidade de análise
            schema: Nome do schema (ex: 'oswaldo_analitico')
            
        Raises:
            ValueError: Se schema não for analítico
        """
        super().__init__(session, entity_class)
        self.schema = schema
        self._validate_schema()

    def _validate_schema(self) -> None:
        """Valida que schema é analítico, nunca operacional.
        
        Raises:
            ValueError: Se schema não é analítico
        """
        if "analitico" not in self.schema.lower() and "analytics" not in self.schema.lower():
            raise ValueError(
                f"❌ AnalyticsDataAccess só usa schemas *_analitico, "
                f"recebeu: {self.schema}"
            )

    def create(self, entity_data: dict[str, Any]) -> T:
        """❌ REJEITA criação em schema analítico.
        
        Raises:
            PermissionError: Sempre
        """
        raise PermissionError(
            f"❌ AnalyticsDataAccess é READ-ONLY. "
            f"Não é permitido criar em {self.schema}. "
            "Use OperationalDataAccess para escrever dados."
        )

    def update(self, entity_id: str | int, updates: dict[str, Any]) -> Optional[T]:
        """❌ REJEITA atualização em schema analítico.
        
        Raises:
            PermissionError: Sempre
        """
        raise PermissionError(
            f"❌ AnalyticsDataAccess é READ-ONLY. "
            f"Não é permitido atualizar em {self.schema}. "
            "Use OperationalDataAccess para escrever dados."
        )

    def delete(self, entity_id: str | int) -> bool:
        """❌ REJEITA deleção em schema analítico.
        
        Raises:
            PermissionError: Sempre
        """
        raise PermissionError(
            f"❌ AnalyticsDataAccess é READ-ONLY. "
            f"Não é permitido deletar em {self.schema}. "
            "Use OperationalDataAccess para escrever dados."
        )

    def read(self, entity_id: str | int) -> Optional[T]:
        """✅ Lê entidade do schema analítico.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            Entidade ou None se não encontrada
        """
        try:
            entity = self.session.query(self.entity_class).get(entity_id)
            if entity:
                logger.debug(
                    f"✅ Read {self.entity_class.__name__} {entity_id} from {self.schema}"
                )
            return entity
        except Exception as e:
            logger.error(f"❌ Error reading {self.entity_class.__name__}: {e}")
            raise

    def read_all_denormalized(
        self,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: int = 1000,
    ) -> list[T]:
        """Lê múltiplas entidades denormalizadas otimizadas para BI.
        
        Args:
            filters: Filtros adicionais {coluna: valor}
            order_by: Coluna para ordenar
            limit: Máximo de registros (BI queries podem ser grandes)
            
        Returns:
            Lista de entidades (denormalizadas)
        """
        from sqlalchemy import select, desc

        try:
            query = select(self.entity_class)

            if filters:
                for key, value in filters.items():
                    if hasattr(self.entity_class, key):
                        query = query.where(getattr(self.entity_class, key) == value)

            if order_by:
                if order_by.startswith("-"):
                    query = query.order_by(desc(getattr(self.entity_class, order_by[1:])))
                else:
                    query = query.order_by(getattr(self.entity_class, order_by))

            query = query.limit(limit)
            result = self.session.execute(query).scalars().all()

            logger.debug(
                f"✅ Read {len(result)} denormalized {self.entity_class.__name__}s from {self.schema}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Error in read_all_denormalized: {e}")
            raise

    def aggregate(
        self,
        group_by: str,
        metrics: dict[str, str],
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Agregação para BI (SUM, COUNT, AVG, MAX, MIN).
        
        Args:
            group_by: Coluna para agrupar (ex: 'period_month')
            metrics: Dicionário {nome_resultado: 'funcao(coluna)'}
                     Ex: {'total_pacientes': 'count(paciente_id)'}
            filters: Filtros adicionais
            
        Returns:
            Lista de dicts com agregações
            
        Example:
            >>> dao.aggregate(
            ...     group_by='period_month',
            ...     metrics={
            ...         'total_pacientes': 'count(paciente_id)',
            ...         'avg_dias': 'avg(dias_em_status)'
            ...     },
            ...     filters={'status': 'coordenando'}
            ... )
        """
        try:
            from sqlalchemy import text

            # Monta query SQL de agregação
            metrics_sql = ", ".join(
                f"{metric} as {alias}" for alias, metric in metrics.items()
            )
            filters_sql = ""
            filter_params = {}

            if filters:
                conditions = []
                for i, (col, val) in enumerate(filters.items()):
                    conditions.append(f"{col} = :param_{i}")
                    filter_params[f"param_{i}"] = val
                filters_sql = "WHERE " + " AND ".join(conditions) if conditions else ""

            table_name = self.entity_class.__table__.name
            schema_name = self.schema

            sql = f"""
                SELECT {group_by}, {metrics_sql}
                FROM {schema_name}.{table_name}
                {filters_sql}
                GROUP BY {group_by}
                ORDER BY {group_by} DESC
            """

            result = self.session.execute(text(sql), filter_params)
            rows = result.fetchall()

            logger.debug(
                f"✅ Aggregation query returned {len(rows)} groups from {self.schema}"
            )

            # Converte para lista de dicts
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Error in aggregate: {e}")
            raise

    def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        """Conta entidades com filtros opcionais.
        
        Args:
            filters: Filtros {coluna: valor}
            
        Returns:
            Número de entidades
        """
        try:
            from sqlalchemy import select, func

            query = select(func.count()).select_from(self.entity_class)

            if filters:
                for key, value in filters.items():
                    if hasattr(self.entity_class, key):
                        query = query.where(getattr(self.entity_class, key) == value)

            result = self.session.execute(query).scalar()
            logger.debug(
                f"✅ Counted {result} {self.entity_class.__name__}s in {self.schema}"
            )
            return result or 0

        except Exception as e:
            logger.error(f"❌ Error in count: {e}")
            raise

    def get_statistics(
        self,
        column: str,
        filters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Retorna estatísticas de uma coluna (MIN, MAX, AVG, COUNT).
        
        Args:
            column: Nome da coluna numérica
            filters: Filtros opcionais
            
        Returns:
            Dict com min, max, avg, count, sum
        """
        try:
            from sqlalchemy import select, func

            query = select(
                func.min(getattr(self.entity_class, column)).label("min_val"),
                func.max(getattr(self.entity_class, column)).label("max_val"),
                func.avg(getattr(self.entity_class, column)).label("avg_val"),
                func.count(getattr(self.entity_class, column)).label("count_val"),
                func.sum(getattr(self.entity_class, column)).label("sum_val"),
            )

            if filters:
                for key, value in filters.items():
                    if hasattr(self.entity_class, key):
                        query = query.where(getattr(self.entity_class, key) == value)

            result = self.session.execute(query).first()

            logger.debug(
                f"✅ Statistics computed for {column} in {self.schema}"
            )

            return {
                "min": result[0],
                "max": result[1],
                "avg": result[2],
                "count": result[3],
                "sum": result[4],
            } if result else {}

        except Exception as e:
            logger.error(f"❌ Error in get_statistics: {e}")
            raise
