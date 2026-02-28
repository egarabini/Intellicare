"""Armazenamento de eventos no banco de dados."""

import logging
import inspect
from datetime import datetime, UTC
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


from geralda.events.event_enricher import EnrichedEvent
from geralda.events.event_types import IntelliCareEvent


logger = logging.getLogger(__name__)


class EventStore:
    """
    Persistência de eventos no banco de dados.

    Salva eventos processados e seus resultados.
    """

    def __init__(self, db_session_factory):
        """
        Inicializa armazenamento.

        Args:
            db_session_factory: Factory de sessões do banco
        """
        self._session_factory = db_session_factory

    async def _resolve_session(self):
        session_or_ctx = self._session_factory()
        if inspect.isawaitable(session_or_ctx):
            session_or_ctx = await session_or_ctx

        if hasattr(session_or_ctx, "__aenter__") and hasattr(session_or_ctx, "__aexit__"):
            async with session_or_ctx as session:
                yield session
            return

        yield session_or_ctx

    async def save(
        self,
        event: IntelliCareEvent,
        enriched: EnrichedEvent,
        result_status: str,
        context_activated: Optional[str] = None,
        protocol_executed: Optional[str] = None,
        actions_taken: list[Any] = None,
    ) -> None:
        """
        Salva evento processado no banco.

        Args:
            event: Evento original
            enriched: Evento enriquecido
            result_status: Status do processamento
            context_activated: Contexto ativado
            protocol_executed: Protocolo executado
            actions_taken: Lista de ações executadas
        """
        async for session in self._resolve_session():
            try:
                # Inserir na tabela journey_events
                # Nota: Futuramente criar modelo SQLAlchemy
                query = text("""
                    INSERT INTO journey_events (
                        event_id,
                        event_type,
                        source,
                        patient_id,
                        timestamp,
                        payload,
                        correlation_id,
                        idempotency_key,
                        metadata,
                        processing_status,
                        context_activated,
                        protocol_executed,
                        actions_taken,
                        processed_at
                    ) VALUES (
                        :event_id,
                        :event_type,
                        :source,
                        :patient_id,
                        :timestamp,
                        :payload,
                        :correlation_id,
                        :idempotency_key,
                        :metadata,
                        :processing_status,
                        :context_activated,
                        :protocol_executed,
                        :actions_taken,
                        :processed_at
                    )
                """)

                await session.execute(query, {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "source": event.source,
                    "patient_id": event.patient_id,
                    "timestamp": event.timestamp,
                    "payload": enriched.original_event.payload,  # JSONB
                    "correlation_id": event.correlation_id,
                    "idempotency_key": event.idempotency_key,
                    "metadata": event.metadata,
                    "processing_status": result_status,
                    "context_activated": context_activated,
                    "protocol_executed": protocol_executed,
                    "actions_taken": actions_taken or [],
                    "processed_at": datetime.now(UTC),
                })

                await session.commit()
                logger.debug(f"Event saved to DB: {event.event_id}")

            except Exception as e:
                if hasattr(session, "rollback"):
                    await session.rollback()
                logger.error(f"Error saving event to DB: {e}")

    async def save_error(
        self,
        event_id: str,
        raw_event: dict[str, Any],
        error_message: str,
    ) -> None:
        """
        Salva registro de falha no processamento.

        Args:
            event_id: ID do evento
            raw_event: Evento bruto
            error_message: Mensagem de erro
        """
        async for session in self._resolve_session():
            try:
                query = text("""
                    INSERT INTO journey_events (
                        event_id,
                        event_type,
                        source,
                        patient_id,
                        timestamp,
                        payload,
                        idempotency_key,
                        metadata,
                        processing_status,
                        error_message,
                        processed_at
                    ) VALUES (
                        :event_id,
                        :event_type,
                        :source,
                        :patient_id,
                        :timestamp,
                        :payload,
                        :idempotency_key,
                        :metadata,
                        :processing_status,
                        :error_message,
                        :processed_at
                    )
                """)

                await session.execute(query, {
                    "event_id": event_id,
                    "event_type": raw_event.get("event_type", "unknown"),
                    "source": raw_event.get("source", "unknown"),
                    "patient_id": raw_event.get("patient_id", ""),
                    "timestamp": datetime.now(UTC),
                    "payload": raw_event.get("payload", {}),
                    "idempotency_key": raw_event.get("idempotency_key", ""),
                    "metadata": raw_event.get("metadata", {}),
                    "processing_status": "failed",
                    "error_message": error_message,
                    "processed_at": datetime.now(UTC),
                })

                await session.commit()
                logger.debug(f"Event error saved: {event_id}")

            except Exception as e:
                if hasattr(session, "rollback"):
                    await session.rollback()
                logger.error(f"Error saving event error: {e}")

    async def get_patient_events(
        self,
        patient_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Busca eventos de um paciente.

        Args:
            patient_id: ID do paciente
            limit: Limite de registros
            offset: Offset para paginação

        Returns:
            Lista de eventos
        """
        async for session in self._resolve_session():
            try:
                query = text("""
                    SELECT
                        event_id,
                        event_type,
                        source,
                        timestamp,
                        payload,
                        processing_status,
                        context_activated,
                        protocol_executed,
                        actions_taken,
                        error_message
                    FROM journey_events
                    WHERE patient_id = :patient_id
                    ORDER BY timestamp DESC
                    LIMIT :limit OFFSET :offset
                """)

                result = await session.execute(query, {
                    "patient_id": patient_id,
                    "limit": limit,
                    "offset": offset,
                })

                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]

            except Exception as e:
                logger.error(f"Error getting patient events: {e}")
                return []
