from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from gestor.db import get_db
from gestor.services.sector_service import SectorService
from gestor.schemas.sector_schemas import SectorCreate, SectorUpdate, SectorResponse, SectorListResponse
from gestor.middleware import require_permission

router = APIRouter(prefix="/sectors", tags=["Sectors"])

@router.get("", response_model=SectorListResponse)
@require_permission("gestor.setores")
async def list_sectors(request: Request, db: AsyncSession = Depends(get_db)):
    service = SectorService(db)
    sectors = await service.list_sectors()
    return SectorListResponse(sectors=sectors, total=len(sectors))

@router.post("", response_model=SectorResponse, status_code=status.HTTP_201_CREATED)
@require_permission("gestor.setores")
async def create_sector(request: Request, sector_in: SectorCreate, db: AsyncSession = Depends(get_db)):
    service = SectorService(db)
    return await service.create_sector(sector_in)

@router.patch("/{sector_id}", response_model=SectorResponse)
@require_permission("gestor.setores")
async def update_sector(request: Request, sector_id: UUID, sector_in: SectorUpdate, db: AsyncSession = Depends(get_db)):
    service = SectorService(db)
    sector = await service.update_sector(sector_id, sector_in)
    if not sector:
        raise HTTPException(status_code=404, detail="Setor não encontrado")
    return sector
