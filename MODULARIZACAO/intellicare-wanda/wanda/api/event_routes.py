"""API routes for Event Consumer (EF-W006)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/events", tags=["events"])


class SimulateEventRequest(BaseModel):
    event_type: str
    patient_id: str
    source_module: str = "intellicare-test"
    payload: dict = {}
    priority: str = "medium"


def _get_consumer(request: Request):  # type: ignore[return]
    consumer = getattr(request.app.state, "event_consumer", None)
    if consumer is None:
        raise HTTPException(status_code=503, detail="EventConsumer nao disponivel (enable_event_consumer=False)")
    return consumer


def _get_coordinator(request: Request):  # type: ignore[return]
    coordinator = getattr(request.app.state, "event_coordinator", None)
    if coordinator is None:
        raise HTTPException(status_code=503, detail="EventCoordinator nao disponivel")
    return coordinator


@router.get("/stream", summary="Status dos Redis Streams")
async def stream_status(request: Request):
    consumer = _get_consumer(request)
    return consumer.status


@router.get("/coordinations", summary="Historico de coordenacoes recentes")
async def list_coordinations(request: Request, limit: int = 20):
    # Coordination history is stored in DB — return placeholder when no store configured
    return {"message": "Historico disponivel via AlertStore/EventCoordinationModel", "limit": limit}


@router.post("/simulate", summary="Simular evento do ecossistema (dev/test)")
async def simulate_event(body: SimulateEventRequest, request: Request):
    from wanda.events.models import IntelliCareEvent  # noqa: PLC0415

    coordinator = _get_coordinator(request)
    event = IntelliCareEvent(
        event_type=body.event_type,
        patient_id=body.patient_id,
        source_module=body.source_module,
        payload=body.payload,
        priority=body.priority,
    )
    result = await coordinator.coordinate(event)
    return {
        "event_id": result.event_id,
        "event_type": result.event_type,
        "status": result.status,
        "agents_notified": result.agents_notified,
        "agents_failed": result.agents_failed,
        "workflow_triggered": result.workflow_triggered,
        "coordination_time_ms": result.coordination_time_ms,
    }
