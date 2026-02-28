"""SectorService — CRUD de setores organizacionais do tenant."""

import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.models.sector import Sector
from gestor.schemas.sector_schemas import SectorCreate, SectorUpdate


class SectorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_sectors(self, active_only: bool = True) -> list[Sector]:
        q = select(Sector)
        if active_only:
            q = q.where(Sector.active == True)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_sector(self, sector_id: uuid.UUID) -> Sector:
        sector = await self._session.get(Sector, sector_id)
        if not sector:
            raise HTTPException(404, f"Setor {sector_id} não encontrado")
        return sector

    async def create_sector(self, data: SectorCreate) -> Sector:
        # Validar hierarquia máxima de 2 níveis
        if data.parent_id:
            parent = await self.get_sector(data.parent_id)
            if parent.parent_id:
                raise HTTPException(
                    400,
                    "Hierarquia de setores suporta no máximo 2 níveis",
                )

        sector = Sector(
            name=data.name,
            type=data.type,
            parent_id=data.parent_id,
            responsavel_id=data.responsavel_id,
        )
        self._session.add(sector)
        await self._session.flush()
        await self._session.refresh(sector)
        return sector

    async def update_sector(self, sector_id: uuid.UUID, data: SectorUpdate) -> Sector:
        sector = await self.get_sector(sector_id)

        if data.parent_id and data.parent_id != sector.parent_id:
            parent = await self.get_sector(data.parent_id)
            if parent.parent_id:
                raise HTTPException(400, "Hierarquia de setores suporta no máximo 2 níveis")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(sector, field, value)

        await self._session.flush()
        await self._session.refresh(sector)
        return sector
