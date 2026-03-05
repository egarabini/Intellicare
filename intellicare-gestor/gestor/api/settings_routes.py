"""Rotas de configurações do tenant — 2 endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.api.deps import get_db, get_audit
from gestor.schemas.settings_schemas import TenantSettingResponse as SettingResponse, SettingsBulkUpdate
from gestor.services.audit_service import AuditService
from gestor.services.settings_service import SettingsService

router = APIRouter()


def _settings_service(session: AsyncSession = Depends(get_db)) -> SettingsService:
    return SettingsService(session)


@router.get("/settings", response_model=list[SettingResponse])
async def list_settings(
    category: Optional[str] = None,
    svc: SettingsService = Depends(_settings_service),
):
    return await svc.list_settings(category=category)


@router.patch("/settings", response_model=list[SettingResponse])
async def update_settings(
    data: SettingsBulkUpdate,
    request: Request,
    svc: SettingsService = Depends(_settings_service),
    audit: AuditService = Depends(get_audit),
):
    updated = await svc.bulk_update(data.settings)
    await audit.log_action(
        "settings.updated",
        resource_type="settings",
        details={"keys": list(data.settings.keys())},
        ip_address=request.client.host if request.client else None,
    )
    return updated
