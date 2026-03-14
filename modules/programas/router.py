"""Programas Router — endpoints REST do modulo programas."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from intellicare_core.auth.jwt import get_current_tenant, require_role
from intellicare_core.contracts.base import TenantContext
from .schemas import CoverageReport, EnrollRequest, EnrollmentResponse, OverduePatient, ProgramCreate, ProgramResponse
from .service import ProgramasService

router = APIRouter(tags=["programas"])
_svc = ProgramasService()
Gestor = Annotated[TenantContext, Depends(require_role("TENANT_GESTOR"))]


async def _clinico_or_gestor(
    ctx: Annotated[TenantContext, Depends(get_current_tenant)],
) -> TenantContext:
    if ctx.has_role("CLINICO") or ctx.has_role("TENANT_GESTOR"):
        return ctx
    raise HTTPException(status_code=403, detail="Role 'CLINICO' ou 'TENANT_GESTOR' necessaria")


ClinicoOrGestor = Annotated[TenantContext, Depends(_clinico_or_gestor)]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "programas", "version": "1.0.0"}


@router.get("/", response_model=list[ProgramResponse])
async def list_programs(ctx: ClinicoOrGestor, active_only: bool = True):
    return await _svc.list_programs(ctx, active_only)


@router.post("/", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(body: ProgramCreate, ctx: Gestor):
    return await _svc.create_program(ctx, body.model_dump())


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_program(program_id: int, ctx: Gestor) -> Response:
    await _svc.deactivate_program(ctx, program_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{program_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_patient(program_id: int, body: EnrollRequest, ctx: ClinicoOrGestor):
    return await _svc.enroll(ctx, program_id, body.model_dump())


@router.get("/{program_id}/patients", response_model=list[EnrollmentResponse])
async def list_enrolled(program_id: int, ctx: ClinicoOrGestor, status: str = "active"):
    return await _svc.list_enrolled(ctx, program_id, status)


@router.delete("/{program_id}/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def discharge_patient(program_id: int, patient_id: UUID, ctx: ClinicoOrGestor) -> Response:
    await _svc.discharge(ctx, program_id, str(patient_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{program_id}/overdue", response_model=list[OverduePatient])
async def overdue_patients(program_id: int, ctx: ClinicoOrGestor, threshold_days: int = 30):
    return await _svc.overdue_patients(ctx, program_id, threshold_days)


@router.get("/{program_id}/coverage", response_model=CoverageReport)
async def coverage_report(program_id: int, ctx: Gestor, threshold_days: int = 30):
    try:
        return await _svc.coverage(ctx, program_id, threshold_days)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
