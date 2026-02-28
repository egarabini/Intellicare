"""SettingsService — Configurações chave-valor do tenant."""

import uuid
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.models.settings import TenantSetting
from gestor.schemas.settings_schemas import SettingUpdate


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_settings(self, category: Optional[str] = None) -> list[TenantSetting]:
        q = select(TenantSetting)
        if category:
            q = q.where(TenantSetting.category == category)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_setting(self, key: str) -> TenantSetting:
        result = await self._session.execute(
            select(TenantSetting).where(TenantSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        if not setting:
            raise HTTPException(404, f"Configuração '{key}' não encontrada")
        return setting

    async def update_setting(
        self,
        key: str,
        data: SettingUpdate,
        updated_by: Optional[uuid.UUID] = None,
    ) -> TenantSetting:
        result = await self._session.execute(
            select(TenantSetting).where(TenantSetting.key == key)
        )
        setting = result.scalar_one_or_none()

        if setting is None:
            raise HTTPException(404, f"Configuração '{key}' não encontrada")

        setting.value = data.value
        if data.value_type:
            setting.value_type = data.value_type
        setting.updated_at = datetime.now(UTC)
        setting.updated_by = updated_by

        await self._session.flush()
        await self._session.refresh(setting)
        return setting

    async def bulk_update(
        self,
        updates: dict[str, str],
        updated_by: Optional[uuid.UUID] = None,
    ) -> list[TenantSetting]:
        updated = []
        for key, value in updates.items():
            try:
                setting = await self.update_setting(
                    key, SettingUpdate(value=value), updated_by
                )
                updated.append(setting)
            except HTTPException:
                pass  # Ignorar chaves inexistentes no bulk
        return updated
