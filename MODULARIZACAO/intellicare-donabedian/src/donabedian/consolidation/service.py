"""
Consolidation service for donabedian module.

Specializes ConsolidationConsumer for donabedian entities:
- Consolidates operacional (transactional) → analitico (denormalized)
- Handles Pilar, Indicator, Measurement consolidation
- Maintains denormalized columns: consolidated_at, consolidation_source
"""

import asyncio
import json
import logging
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import text, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class DonabedianConsolidationService:
    """
    Consolidates donabedian data from operacional to analitico schema.
    
    Flow:
    1. Listen to Redis events (pilar.create, pilar.update, pilar.delete)
    2. Read from donabedian_operacional
    3. Write/update to donabedian_analitico
    4. Set consolidated_at timestamp
    """

    def __init__(self, db_url: str):
        """
        Initialize service.
        
        Args:
            db_url: PostgreSQL connection URL
        """
        self.db_url = db_url
        self._engine: Optional[Any] = None
        self._session_maker: Optional[Any] = None

    async def _get_engine(self):
        """Get or create async SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.db_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
            )
        return self._engine

    async def _get_session(self) -> AsyncSession:
        """Get new async session."""
        if self._session_maker is None:
            engine = await self._get_engine()
            self._session_maker = sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_maker()

    async def consolidate_pilar_create(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Pilar CREATE: INSERT from operacional to analitico.
        
        SQL:
            INSERT INTO donabedian_analitico.pilares
            SELECT * FROM donabedian_operacional.pilares
            WHERE id = $1 AND valid_to IS NULL
        """
        session = await self._get_session()
        try:
            # Get from operacional
            result = await session.execute(
                text("""
                    SELECT 
                        id, nome, descricao, tipo, ordem_exibicao, ativo,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.pilares
                    WHERE id = :entity_id AND valid_to IS NULL
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Pilar {entity_id} not found in operacional")
                return False

            # Insert/upsert to analitico
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.pilares 
                    (id, nome, descricao, tipo, ordem_exibicao, ativo,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :nome, :descricao, :tipo, :ordem_exibicao, :ativo,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'pilar.create')
                    ON CONFLICT (id) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        descricao = EXCLUDED.descricao,
                        tipo = EXCLUDED.tipo,
                        ordem_exibicao = EXCLUDED.ordem_exibicao,
                        ativo = EXCLUDED.ativo,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        rowversion = EXCLUDED.rowversion,
                        consolidated_at = now(),
                        consolidation_source = 'pilar.create'
                """),
                {
                    "id": str(row[0]),
                    "nome": row[1],
                    "descricao": row[2],
                    "tipo": row[3],
                    "ordem_exibicao": row[4],
                    "ativo": row[5],
                    "created_by": str(row[6]),
                    "created_at": row[7],
                    "updated_by": str(row[8]) if row[8] else None,
                    "updated_at": row[9],
                    "valid_to": row[10],
                    "rowversion": row[11],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated CREATE pilar {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating pilar CREATE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate_pilar_update(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Pilar UPDATE: sync changes to analitico.
        
        SQL: Similar to CREATE but ensures record exists
        """
        session = await self._get_session()
        try:
            # Get updated record from operacional
            result = await session.execute(
                text("""
                    SELECT 
                        id, nome, descricao, tipo, ordem_exibicao, ativo,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.pilares
                    WHERE id = :entity_id
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Pilar {entity_id} not found in operacional after update")
                return False

            # Upsert to analitico
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.pilares 
                    (id, nome, descricao, tipo, ordem_exibicao, ativo,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :nome, :descricao, :tipo, :ordem_exibicao, :ativo,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'pilar.update')
                    ON CONFLICT (id) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        descricao = EXCLUDED.descricao,
                        tipo = EXCLUDED.tipo,
                        ordem_exibicao = EXCLUDED.ordem_exibicao,
                        ativo = EXCLUDED.ativo,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        valid_to = EXCLUDED.valid_to,
                        rowversion = EXCLUDED.rowversion,
                        consolidated_at = now(),
                        consolidation_source = 'pilar.update'
                """),
                {
                    "id": str(row[0]),
                    "nome": row[1],
                    "descricao": row[2],
                    "tipo": row[3],
                    "ordem_exibicao": row[4],
                    "ativo": row[5],
                    "created_by": str(row[6]),
                    "created_at": row[7],
                    "updated_by": str(row[8]) if row[8] else None,
                    "updated_at": row[9],
                    "valid_to": row[10],
                    "rowversion": row[11],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated UPDATE pilar {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating pilar UPDATE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate_pilar_delete(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Pilar DELETE: update valid_to in analitico.
        
        SQL: Set valid_to = now() for soft delete
        """
        session = await self._get_session()
        try:
            # Get deleted record (with valid_to set)
            result = await session.execute(
                text("""
                    SELECT 
                        id, nome, descricao, tipo, ordem_exibicao, ativo,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.pilares
                    WHERE id = :entity_id
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Pilar {entity_id} not found in operacional")
                return False

            # Upsert to analitico with valid_to set
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.pilares 
                    (id, nome, descricao, tipo, ordem_exibicao, ativo,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :nome, :descricao, :tipo, :ordem_exibicao, :ativo,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'pilar.delete')
                    ON CONFLICT (id) DO UPDATE SET
                        valid_to = EXCLUDED.valid_to,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        consolidated_at = now(),
                        consolidation_source = 'pilar.delete'
                """),
                {
                    "id": str(row[0]),
                    "nome": row[1],
                    "descricao": row[2],
                    "tipo": row[3],
                    "ordem_exibicao": row[4],
                    "ativo": row[5],
                    "created_by": str(row[6]),
                    "created_at": row[7],
                    "updated_by": str(row[8]) if row[8] else None,
                    "updated_at": row[9],
                    "valid_to": row[10],
                    "rowversion": row[11],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated DELETE pilar {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating pilar DELETE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate_indicator_create(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Indicator CREATE: INSERT from operacional to analitico.
        
        SQL:
            INSERT INTO donabedian_analitico.indicadores
            SELECT * FROM donabedian_operacional.indicadores
            WHERE id = $1 AND valid_to IS NULL
        """
        session = await self._get_session()
        try:
            # Get from operacional
            result = await session.execute(
                text("""
                    SELECT 
                        id, nome, descricao, formula, unidade, valor_meta, operador_meta,
                        dimensao_triado, ativo,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.indicadores
                    WHERE id = :entity_id AND valid_to IS NULL
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Indicator {entity_id} not found in operacional")
                return False

            # Insert/upsert to analitico
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.indicadores 
                    (id, nome, descricao, formula, unidade, valor_meta, operador_meta,
                     dimensao_triado, ativo,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :nome, :descricao, :formula, :unidade, :valor_meta, :operador_meta,
                            :dimensao_triado, :ativo,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'indicator.create')
                    ON CONFLICT (id) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        descricao = EXCLUDED.descricao,
                        formula = EXCLUDED.formula,
                        unidade = EXCLUDED.unidade,
                        valor_meta = EXCLUDED.valor_meta,
                        operador_meta = EXCLUDED.operador_meta,
                        dimensao_triado = EXCLUDED.dimensao_triado,
                        ativo = EXCLUDED.ativo,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        rowversion = EXCLUDED.rowversion,
                        consolidated_at = now(),
                        consolidation_source = 'indicator.create'
                """),
                {
                    "id": str(row[0]),
                    "nome": row[1],
                    "descricao": row[2],
                    "formula": row[3],
                    "unidade": row[4],
                    "valor_meta": row[5],
                    "operador_meta": row[6],
                    "dimensao_triado": row[7],
                    "ativo": row[8],
                    "created_by": str(row[9]),
                    "created_at": row[10],
                    "updated_by": str(row[11]) if row[11] else None,
                    "updated_at": row[12],
                    "valid_to": row[13],
                    "rowversion": row[14],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated CREATE indicator {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating indicator CREATE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate_indicator_update(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Indicator UPDATE: sync changes to analitico.
        """
        session = await self._get_session()
        try:
            # Get updated record from operacional
            result = await session.execute(
                text("""
                    SELECT 
                        id, nome, descricao, formula, unidade, valor_meta, operador_meta,
                        dimensao_triado, ativo,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.indicadores
                    WHERE id = :entity_id
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Indicator {entity_id} not found in operacional after update")
                return False

            # Upsert to analitico
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.indicadores 
                    (id, nome, descricao, formula, unidade, valor_meta, operador_meta,
                     dimensao_triado, ativo,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :nome, :descricao, :formula, :unidade, :valor_meta, :operador_meta,
                            :dimensao_triado, :ativo,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'indicator.update')
                    ON CONFLICT (id) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        descricao = EXCLUDED.descricao,
                        formula = EXCLUDED.formula,
                        unidade = EXCLUDED.unidade,
                        valor_meta = EXCLUDED.valor_meta,
                        operador_meta = EXCLUDED.operador_meta,
                        dimensao_triado = EXCLUDED.dimensao_triado,
                        ativo = EXCLUDED.ativo,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        valid_to = EXCLUDED.valid_to,
                        rowversion = EXCLUDED.rowversion,
                        consolidated_at = now(),
                        consolidation_source = 'indicator.update'
                """),
                {
                    "id": str(row[0]),
                    "nome": row[1],
                    "descricao": row[2],
                    "formula": row[3],
                    "unidade": row[4],
                    "valor_meta": row[5],
                    "operador_meta": row[6],
                    "dimensao_triado": row[7],
                    "ativo": row[8],
                    "created_by": str(row[9]),
                    "created_at": row[10],
                    "updated_by": str(row[11]) if row[11] else None,
                    "updated_at": row[12],
                    "valid_to": row[13],
                    "rowversion": row[14],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated UPDATE indicator {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating indicator UPDATE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate_indicator_delete(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Indicator DELETE: update valid_to in analitico.
        """
        session = await self._get_session()
        try:
            # Get deleted record (with valid_to set)
            result = await session.execute(
                text("""
                    SELECT 
                        id, nome, descricao, formula, unidade, valor_meta, operador_meta,
                        dimensao_triado, ativo,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.indicadores
                    WHERE id = :entity_id
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Indicator {entity_id} not found in operacional")
                return False

            # Upsert to analitico with valid_to set
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.indicadores 
                    (id, nome, descricao, formula, unidade, valor_meta, operador_meta,
                     dimensao_triado, ativo,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :nome, :descricao, :formula, :unidade, :valor_meta, :operador_meta,
                            :dimensao_triado, :ativo,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'indicator.delete')
                    ON CONFLICT (id) DO UPDATE SET
                        valid_to = EXCLUDED.valid_to,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        consolidated_at = now(),
                        consolidation_source = 'indicator.delete'
                """),
                {
                    "id": str(row[0]),
                    "nome": row[1],
                    "descricao": row[2],
                    "formula": row[3],
                    "unidade": row[4],
                    "valor_meta": row[5],
                    "operador_meta": row[6],
                    "dimensao_triado": row[7],
                    "ativo": row[8],
                    "created_by": str(row[9]),
                    "created_at": row[10],
                    "updated_by": str(row[11]) if row[11] else None,
                    "updated_at": row[12],
                    "valid_to": row[13],
                    "rowversion": row[14],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated DELETE indicator {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating indicator DELETE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate_measurement_create(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Measurement CREATE: INSERT from operacional to analitico.
        """
        session = await self._get_session()
        try:
            # Get from operacional
            result = await session.execute(
                text("""
                    SELECT 
                        id, indicator_id, valor, periodo_inicio, periodo_fim, tipo_periodo, status,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.medicoes
                    WHERE id = :entity_id AND valid_to IS NULL
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Measurement {entity_id} not found in operacional")
                return False

            # Insert/upsert to analitico
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.medicoes 
                    (id, indicator_id, valor, periodo_inicio, periodo_fim, tipo_periodo, status,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :indicator_id, :valor, :periodo_inicio, :periodo_fim, :tipo_periodo, :status,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'measurement.create')
                    ON CONFLICT (id) DO UPDATE SET
                        indicator_id = EXCLUDED.indicator_id,
                        valor = EXCLUDED.valor,
                        periodo_inicio = EXCLUDED.periodo_inicio,
                        periodo_fim = EXCLUDED.periodo_fim,
                        tipo_periodo = EXCLUDED.tipo_periodo,
                        status = EXCLUDED.status,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        rowversion = EXCLUDED.rowversion,
                        consolidated_at = now(),
                        consolidation_source = 'measurement.create'
                """),
                {
                    "id": str(row[0]),
                    "indicator_id": str(row[1]),
                    "valor": row[2],
                    "periodo_inicio": row[3],
                    "periodo_fim": row[4],
                    "tipo_periodo": row[5],
                    "status": row[6],
                    "created_by": str(row[7]),
                    "created_at": row[8],
                    "updated_by": str(row[9]) if row[9] else None,
                    "updated_at": row[10],
                    "valid_to": row[11],
                    "rowversion": row[12],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated CREATE measurement {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating measurement CREATE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate_measurement_update(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Measurement UPDATE: sync changes to analitico.
        """
        session = await self._get_session()
        try:
            # Get updated record from operacional
            result = await session.execute(
                text("""
                    SELECT 
                        id, indicator_id, valor, periodo_inicio, periodo_fim, tipo_periodo, status,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.medicoes
                    WHERE id = :entity_id
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Measurement {entity_id} not found in operacional after update")
                return False

            # Upsert to analitico
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.medicoes 
                    (id, indicator_id, valor, periodo_inicio, periodo_fim, tipo_periodo, status,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :indicator_id, :valor, :periodo_inicio, :periodo_fim, :tipo_periodo, :status,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'measurement.update')
                    ON CONFLICT (id) DO UPDATE SET
                        indicator_id = EXCLUDED.indicator_id,
                        valor = EXCLUDED.valor,
                        periodo_inicio = EXCLUDED.periodo_inicio,
                        periodo_fim = EXCLUDED.periodo_fim,
                        tipo_periodo = EXCLUDED.tipo_periodo,
                        status = EXCLUDED.status,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        valid_to = EXCLUDED.valid_to,
                        rowversion = EXCLUDED.rowversion,
                        consolidated_at = now(),
                        consolidation_source = 'measurement.update'
                """),
                {
                    "id": str(row[0]),
                    "indicator_id": str(row[1]),
                    "valor": row[2],
                    "periodo_inicio": row[3],
                    "periodo_fim": row[4],
                    "tipo_periodo": row[5],
                    "status": row[6],
                    "created_by": str(row[7]),
                    "created_at": row[8],
                    "updated_by": str(row[9]) if row[9] else None,
                    "updated_at": row[10],
                    "valid_to": row[11],
                    "rowversion": row[12],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated UPDATE measurement {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating measurement UPDATE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate_measurement_delete(
        self,
        entity_id: UUID,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Consolidate Measurement DELETE: update valid_to in analitico.
        """
        session = await self._get_session()
        try:
            # Get deleted record (with valid_to set)
            result = await session.execute(
                text("""
                    SELECT 
                        id, indicator_id, valor, periodo_inicio, periodo_fim, tipo_periodo, status,
                        created_by, created_at, updated_by, updated_at,
                        valid_to, rowversion
                    FROM donabedian_operacional.medicoes
                    WHERE id = :entity_id
                """),
                {"entity_id": str(entity_id)}
            )
            
            row = result.first()
            if not row:
                logger.warning(f"Measurement {entity_id} not found in operacional")
                return False

            # Upsert to analitico with valid_to set
            await session.execute(
                text("""
                    INSERT INTO donabedian_analitico.medicoes 
                    (id, indicator_id, valor, periodo_inicio, periodo_fim, tipo_periodo, status,
                     created_by, created_at, updated_by, updated_at,
                     valid_to, rowversion, consolidated_at, consolidation_source)
                    VALUES (:id, :indicator_id, :valor, :periodo_inicio, :periodo_fim, :tipo_periodo, :status,
                            :created_by, :created_at, :updated_by, :updated_at,
                            :valid_to, :rowversion, now(), 'measurement.delete')
                    ON CONFLICT (id) DO UPDATE SET
                        valid_to = EXCLUDED.valid_to,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at,
                        consolidated_at = now(),
                        consolidation_source = 'measurement.delete'
                """),
                {
                    "id": str(row[0]),
                    "indicator_id": str(row[1]),
                    "valor": row[2],
                    "periodo_inicio": row[3],
                    "periodo_fim": row[4],
                    "tipo_periodo": row[5],
                    "status": row[6],
                    "created_by": str(row[7]),
                    "created_at": row[8],
                    "updated_by": str(row[9]) if row[9] else None,
                    "updated_at": row[10],
                    "valid_to": row[11],
                    "rowversion": row[12],
                }
            )
            
            await session.commit()
            logger.info(f"✅ Consolidated DELETE measurement {entity_id}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error consolidating measurement DELETE {entity_id}: {e}")
            return False
        finally:
            await session.close()

    async def consolidate(
        self,
        entity_type: str,
        entity_id: UUID,
        operation: str,
        old_values: Optional[dict],
        new_values: Optional[dict],
        timestamp: str
    ) -> bool:
        """
        Route consolidation to appropriate handler.
        
        Args:
            entity_type: Type of entity (Pilar, Indicator, Measurement)
            entity_id: Entity UUID
            operation: CREATE, UPDATE, DELETE
            old_values: Previous values (for UPDATE)
            new_values: New values (for UPDATE/CREATE)
            timestamp: ISO timestamp
            
        Returns:
            True if consolidation succeeded
        """
        if entity_type == "Pilar":
            if operation == "CREATE":
                return await self.consolidate_pilar_create(entity_id, old_values, new_values, timestamp)
            elif operation == "UPDATE":
                return await self.consolidate_pilar_update(entity_id, old_values, new_values, timestamp)
            elif operation == "DELETE":
                return await self.consolidate_pilar_delete(entity_id, old_values, new_values, timestamp)
        
        elif entity_type == "Indicator":
            if operation == "CREATE":
                return await self.consolidate_indicator_create(entity_id, old_values, new_values, timestamp)
            elif operation == "UPDATE":
                return await self.consolidate_indicator_update(entity_id, old_values, new_values, timestamp)
            elif operation == "DELETE":
                return await self.consolidate_indicator_delete(entity_id, old_values, new_values, timestamp)
        
        elif entity_type == "Measurement":
            if operation == "CREATE":
                return await self.consolidate_measurement_create(entity_id, old_values, new_values, timestamp)
            elif operation == "UPDATE":
                return await self.consolidate_measurement_update(entity_id, old_values, new_values, timestamp)
            elif operation == "DELETE":
                return await self.consolidate_measurement_delete(entity_id, old_values, new_values, timestamp)
        
        logger.warning(f"Unknown consolidation: {entity_type} {operation}")
        return False

    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
        logger.info("Consolidation service closed")
