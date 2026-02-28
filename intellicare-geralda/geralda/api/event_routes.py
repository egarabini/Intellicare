"""Rotas de API para motor de eventos."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from geralda.events import create_pipeline, emit_event


router = APIRouter(prefix="/api/v1/events", tags=["events"])


# Pipeline singleton
_event_pipeline = None


def get_event_pipeline():
    """Obtém instância singleton do pipeline."""
    global _event_pipeline

    if _event_pipeline is None:
        from geralda.database.base import get_session_factory
        from geralda.config import GeraldaConfig

        config = GeraldaConfig()
        session_factory = get_session_factory(config.database_url)

        # Redis client (opcional)
        try:
            import redis.asyncio as redis

            redis_client = redis.from_url(
                "redis://localhost:6379/0",
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception:
            redis_client = None

        _event_pipeline = create_pipeline(
            db_session_factory=session_factory,
            redis_client=redis_client,
        )

    return _event_pipeline


class EventRequest(BaseModel):
    event_type: str
    patient_id: str
    payload: dict[str, Any]
    source: str = "manual"
    correlation_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


@router.post("")
async def emit_event_endpoint(request: EventRequest):
    """
    Emite um novo evento para processamento.

    O evento será processado pelo pipeline de 7 estágios:
    1. Normalização
    2. Idempotência
    3. Enriquecimento
    4. Interpretação
    5. Execução
    6. Evidência
    7. Persistência
    """
    try:
        pipeline = get_event_pipeline()

        # Criar evento
        event = emit_event(
            event_type=request.event_type,
            patient_id=request.patient_id,
            payload=request.payload,
            source=request.source,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )

        # Processar
        result = await pipeline.process(
            raw_event=request.payload,
            source=request.source,
        )

        return {
            "success": result.status in ("processed", "skipped"),
            "event_id": result.event_id,
            "status": result.status,
            "actions_taken": result.actions_taken,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing event: {str(e)}",
        )


@router.post("/internal/run-event-check")
async def run_event_check():
    """
    Endpoint interno para verificação de eventos.

    Chamado pelo Kestra flow horário.
    Verifica tarefas vencidas, metas não atingidas, etc.
    """
    # TODO: Implementar lógica de verificação
    # - Buscar tarefas vencidas há > 3 dias
    # - Buscar metas não atingidas em 30 dias
    # - Emitir eventos correspondentes

    return {"status": "ok", "checked": True}


@router.get("/{patient_id}")
async def get_patient_events(
    patient_id: str,
    limit: int = Query(100),
    offset: int = Query(0),
):
    """
    Busca eventos de um paciente.

    Retorna timeline de eventos com contexto.
    """
    try:
        pipeline = get_event_pipeline()
        events = await pipeline._store.get_patient_events(
            patient_id=patient_id,
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            "patient_id": patient_id,
            "events": events,
            "total": len(events),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting events: {str(e)}",
        )
