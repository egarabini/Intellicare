from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from conhecimento.api.dependencies import get_protocol_service, get_workflow_service
from conhecimento.models import Protocol, ProtocolSearchRequest, ProtocolStatus
from conhecimento.services import ProtocolService, WorkflowService

router = APIRouter(prefix="/api/v1/protocolos", tags=["protocolos"])


class StatusTransitionRequest(BaseModel):
    actor: str
    target_status: ProtocolStatus
    reason: str


@router.get("", response_model=list[Protocol])
def list_protocols(service: ProtocolService = Depends(get_protocol_service)):
    return service.list_protocols()


@router.get("/{protocol_id}", response_model=Protocol)
def get_protocol(protocol_id: str, service: ProtocolService = Depends(get_protocol_service)):
    protocol = service.get_protocol(protocol_id)
    if protocol is None:
        raise HTTPException(status_code=404, detail="Protocolo nao encontrado")
    return protocol


@router.post("", response_model=Protocol)
def create_protocol(protocol: Protocol, service: ProtocolService = Depends(get_protocol_service)):
    return service.create_protocol(protocol)


@router.put("/{protocol_id}", response_model=Protocol)
def update_protocol(
    protocol_id: str,
    protocol: Protocol,
    author: str,
    changelog: str = "Protocol updated",
    service: ProtocolService = Depends(get_protocol_service),
):
    try:
        return service.update_protocol(protocol_id, protocol, author=author, changelog=changelog)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{protocol_id}/transition", response_model=Protocol)
def transition_status(
    protocol_id: str,
    body: StatusTransitionRequest,
    workflow: WorkflowService = Depends(get_workflow_service),
):
    try:
        return workflow.transition(protocol_id, actor=body.actor, target=body.target_status, reason=body.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{protocol_id}/history")
def protocol_history(protocol_id: str, service: ProtocolService = Depends(get_protocol_service)):
    return [item.model_dump(mode="json") for item in service.history(protocol_id)]


@router.post("/search")
def search(request: ProtocolSearchRequest, service: ProtocolService = Depends(get_protocol_service)):
    return [item.model_dump(mode="json") for item in service.search(request)]

