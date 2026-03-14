"""Gestor Router — endpoints REST do modulo gestor."""
from __future__ import annotations

import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from intellicare_core.auth.jwt import get_current_tenant, require_role
from intellicare_core.contracts.base import TenantContext
from modules.vector.ingest_service import IngestService

from .schemas import InviteUserRequest, UnitProfile
from .service import GestorService

router = APIRouter(tags=["gestor"])
_svc = GestorService()
_ingest = IngestService()

GestorOnly = Annotated[TenantContext, Depends(require_role("TENANT_GESTOR"))]
AnyUser = Annotated[TenantContext, Depends(get_current_tenant)]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "gestor", "version": "1.0.0"}


@router.get("/profile")
async def get_profile(ctx: AnyUser):
    p = await _svc.get_profile(ctx)
    if not p:
        raise HTTPException(404, "Perfil não configurado")
    return p


@router.put("/profile")
async def update_profile(payload: UnitProfile, ctx: GestorOnly):
    return await _svc.upsert_profile(ctx, payload.model_dump())


@router.get("/users")
async def list_users(ctx: GestorOnly):
    from modules.admin.keycloak_client import KeycloakAdminClient

    kc = KeycloakAdminClient()
    gid = await kc.get_tenant_group_id(ctx.tenant_id)
    return await kc.get_group_users(gid) if gid else []


@router.post("/users/invite", status_code=201)
async def invite_user(payload: InviteUserRequest, ctx: GestorOnly):
    from modules.admin.keycloak_client import KeycloakAdminClient

    kc = KeycloakAdminClient()
    gid = await kc.get_tenant_group_id(ctx.tenant_id)
    if not gid:
        raise HTTPException(404, "Grupo do tenant não encontrado no Keycloak")
    user_id = await kc.invite_user(
        group_id=gid,
        email=payload.email,
        name=payload.name,
        role=payload.role,
    )
    return {"user_id": user_id, "email": payload.email, "role": payload.role}


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, ctx: GestorOnly):
    from modules.admin.keycloak_client import KeycloakAdminClient

    kc = KeycloakAdminClient()
    await kc.deactivate_user(user_id)
    return {"user_id": user_id, "active": False}


@router.get("/documents")
async def list_documents(ctx: GestorOnly):
    return await _svc.list_documents(ctx)


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(require_role("TENANT_GESTOR")),
):
    suffix = "." + (file.filename or "doc.txt").rsplit(".", 1)[-1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        return await _ingest.ingest_file(tmp_path, ctx, source_label=file.filename)
    finally:
        os.unlink(tmp_path)


@router.delete("/documents/{source_path:path}")
async def delete_document(source_path: str, ctx: GestorOnly):
    return {"deleted_chunks": await _ingest.delete_document(source_path, ctx)}


@router.get("/reports/usage")
async def usage_report(ctx: GestorOnly, days: int = 30):
    return await _svc.usage_report(ctx, days)
