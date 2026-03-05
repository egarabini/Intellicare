import uuid
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from gestor.models.sector import Sector
from gestor.schemas.sector_schemas import SectorCreate, SectorUpdate

class SectorService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_sector(self, sector_id: uuid.UUID) -> Optional[Sector]:
        result = await self.session.execute(select(Sector).where(Sector.id == sector_id))
        return result.scalar_one_or_none()

    async def list_sectors(self) -> List[Sector]:
        result = await self.session.execute(select(Sector).order_by(Sector.name))
        return list(result.scalars().all())

    async def create_sector(self, sector_data: SectorCreate) -> Sector:
        sector = Sector(**sector_data.model_dump())
        self.session.add(sector)
        await self.session.flush()
        await self.session.refresh(sector)
        return sector

    async def update_sector(self, sector_id: uuid.UUID, sector_data: SectorUpdate) -> Optional[Sector]:
        sector = await self.get_sector(sector_id)
        if not sector:
            return None

        for key, value in sector_data.model_dump(exclude_unset=True).items():
            setattr(sector, key, value)
            
        await self.session.flush()
        await self.session.refresh(sector)
        return sector
