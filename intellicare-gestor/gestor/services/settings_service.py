import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from gestor.models.settings import TenantSetting
from gestor.schemas.settings_schemas import TenantSettingUpdate

class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_settings(self) -> List[TenantSetting]:
        result = await self.session.execute(select(TenantSetting))
        return list(result.scalars().all())

    async def get_setting(self, key: str) -> Optional[TenantSetting]:
        result = await self.session.execute(select(TenantSetting).where(TenantSetting.key == key))
        return result.scalar_one_or_none()

    async def update_setting(self, key: str, setting_data: TenantSettingUpdate, actor_id: Optional[uuid.UUID] = None) -> Optional[TenantSetting]:
        setting = await self.get_setting(key)
        if not setting:
            return None
        
        setting.value = setting_data.value
        setting.value_type = setting_data.value_type
        setting.updated_by = actor_id
        
        await self.session.commit()
        await self.session.refresh(setting)
        return setting
