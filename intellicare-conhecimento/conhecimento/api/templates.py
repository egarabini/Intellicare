from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from conhecimento.api.dependencies import get_careplan_service
from conhecimento.models import CarePlanGenerateRequest
from conhecimento.services import CarePlanService

router = APIRouter(prefix="/api/v1/templates/careplan", tags=["templates"])


@router.get("")
def list_templates(service: CarePlanService = Depends(get_careplan_service)):
    return [item.model_dump(mode="json") for item in service.list_templates()]


@router.get("/{condition}")
def get_template(condition: str, stage: str | None = None, service: CarePlanService = Depends(get_careplan_service)):
    template = service.get_template(condition, stage=stage)
    if template is None:
        raise HTTPException(status_code=404, detail="Template nao encontrado")
    return template.model_dump(mode="json")


@router.post("/generate")
def generate(body: CarePlanGenerateRequest, service: CarePlanService = Depends(get_careplan_service)):
    try:
        return service.generate(body).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

