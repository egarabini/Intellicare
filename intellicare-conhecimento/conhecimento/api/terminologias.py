from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from conhecimento.api.dependencies import get_terminology_service
from conhecimento.models import TerminologySearchRequest, TerminologySystem
from conhecimento.services import TerminologyService

router = APIRouter(prefix="/api/v1/terminologias", tags=["terminologias"])


@router.get("/{system}/{code}")
def get_code(system: TerminologySystem, code: str, service: TerminologyService = Depends(get_terminology_service)):
    item = service.get_code(system, code)
    if item is None:
        raise HTTPException(status_code=404, detail="Codigo nao encontrado")
    return item.model_dump(mode="json")


@router.post("/search")
def search(request: TerminologySearchRequest, service: TerminologyService = Depends(get_terminology_service)):
    return [item.model_dump(mode="json") for item in service.search(request)]


@router.get("/mapeamentos")
def mappings(service: TerminologyService = Depends(get_terminology_service)):
    return [item.model_dump(mode="json") for item in service.mappings()]

