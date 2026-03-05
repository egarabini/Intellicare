"""Rotas de setores — 3 endpoints."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.api.deps import get_db, get_audit
from gestor.schemas.sector_schemas import SectorCreate, SectorResponse, SectorUpdate
from gestor.services.audit_service import AuditService
from gestor.services.sector_service import SectorService

router = APIRouter()


def _sector_service(session: AsyncSession = Depends(get_db)) -> SectorService:
    return SectorService(session)


@router.get("/sectors", response_model=list[SectorResponse])
async def list_sectors(
    active_only: bool = True,
    svc: SectorService = Depends(_sector_service),
):
    return await svc.list_sectors(active_only=active_only)


@router.post("/sectors", response_model=SectorResponse, status_code=201)
async def create_sector(
    data: SectorCreate,
    request: Request,
    svc: SectorService = Depends(_sector_service),
    audit: AuditService = Depends(get_audit),
):
    sector = await svc.create_sector(data)
    await audit.log_action(
        "sector.created",
        resource_type="sector",
        resource_id=str(sector.id),
        details={"name": sector.name, "type": sector.type},
        ip_address=request.client.host if request.client else None,
    )
    return sector


@router.patch("/sectors/{sector_id}", response_model=SectorResponse)
async def update_sector(
    sector_id: uuid.UUID,
    data: SectorUpdate,
    request: Request,
    svc: SectorService = Depends(_sector_service),
    audit: AuditService = Depends(get_audit),
):
    sector = await svc.update_sector(sector_id, data)
    await audit.log_action(
        "sector.updated",
        resource_type="sector",
        resource_id=str(sector_id),
        details=data.model_dump(exclude_none=True),
        ip_address=request.client.host if request.client else None,
    )
    return sector
