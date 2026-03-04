from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from gestor.db import get_db
from gestor.services.settings_service import SettingsService
from gestor.schemas.settings_schemas import TenantSettingUpdate, TenantSettingResponse, TenantSettingListResponse
from gestor.middleware import require_permission

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=TenantSettingListResponse)
@require_permission("gestor.configs")
async def list_settings(request: Request, db: AsyncSession = Depends(get_db)):
    service = SettingsService(db)
    settings = await service.get_all_settings()
    return TenantSettingListResponse(settings=settings, total=len(settings))

@router.patch("/{key}", response_model=TenantSettingResponse)
@require_permission("gestor.configs")
async def update_setting(request: Request, key: str, setting_in: TenantSettingUpdate, db: AsyncSession = Depends(get_db)):
    service = SettingsService(db)
    actor_id = getattr(request.state, "user_id", None)
    
    updated = await service.update_setting(key, setting_in, actor_id=actor_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Configuração {key} não encontrada.")
    return updated
