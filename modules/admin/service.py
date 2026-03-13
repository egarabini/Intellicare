"""TenantService — logica de negocio do modulo admin."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import get_engine
from .keycloak_client import KeycloakAdminClient
from .schemas import TenantCreate, TenantStatusUpdate

logger = logging.getLogger("intellicare.admin.service")

# Caminho para a migration de schema de tenant
import pathlib
_TENANT_MIGRATION = (
    pathlib.Path(__file__).parent / "migrations" / "001_tenant_base.sql"
).read_text()


class TenantService:
    def __init__(self) -> None:
        self._kc = KeycloakAdminClient()

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    async def list_tenants(
        self,
        page: int,
        size: int,
        actor: TenantContext,
    ) -> tuple[list[dict], int]:
        async with get_engine().connect() as conn:
            count = (await conn.execute(
                text("SELECT COUNT(*) FROM public.tenants")
            )).scalar_one()
            rows = (await conn.execute(
                text("""
                    SELECT id, slug, name, status, created_at, updated_at
                    FROM public.tenants
                    ORDER BY created_at DESC
                    LIMIT :size OFFSET :offset
                """),
                {"size": size, "offset": (page - 1) * size},
            )).mappings().all()
        return [dict(r) for r in rows], count

    async def get_tenant(self, slug: str) -> dict | None:
        async with get_engine().connect() as conn:
            row = (await conn.execute(
                text("SELECT * FROM public.tenants WHERE slug = :slug"),
                {"slug": slug},
            )).mappings().first()
        return dict(row) if row else None

    async def get_tenant_users(self, slug: str) -> list[dict]:
        group_id = await self._kc.get_tenant_group_id(slug)
        if not group_id:
            return []
        return await self._kc.get_group_users(group_id)

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    async def create_tenant(
        self,
        payload: TenantCreate,
        actor: TenantContext,
    ) -> dict:
        """
        Cria tenant de forma transacional:
        1. Verifica slug livre
        2. CREATE SCHEMA + migrations
        3. Registra em public.tenants
        4. Cria grupo no Keycloak
        5. Auditoria
        """
        engine = get_engine()

        async with engine.begin() as conn:
            # 1. Verificar slug
            existing = (await conn.execute(
                text("SELECT 1 FROM public.tenants WHERE slug = :slug"),
                {"slug": payload.slug},
            )).first()
            if existing:
                raise ValueError(f"slug '{payload.slug}' ja existe")

            # 2. Schema + migrations
            schema = f"tenant_{payload.slug}"
            await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
            await conn.execute(text(f'SET search_path TO "{schema}", public'))
            await conn.execute(text(_TENANT_MIGRATION))
            await conn.execute(text("SET search_path TO public"))

            # 3. Registrar tenant
            row = (await conn.execute(
                text("""
                    INSERT INTO public.tenants (slug, name)
                    VALUES (:slug, :name)
                    RETURNING id, slug, name, status, created_at, updated_at
                """),
                {"slug": payload.slug, "name": payload.name},
            )).mappings().first()
            tenant = dict(row)  # type: ignore[arg-type]

            # 4. Grupo Keycloak (dentro do bloco begin — se falhar, rollback)
            try:
                group_id = await self._kc.create_tenant_group(payload.slug)
                logger.info("Grupo Keycloak criado: %s (id=%s)", payload.slug, group_id)
            except Exception as exc:
                raise RuntimeError(f"Falha ao criar grupo no Keycloak: {exc}") from exc

            # 5. Auditoria
            await self._audit(conn, actor, "tenant.create", "tenant", payload.slug, {
                "name": payload.name,
                "gestor_email": payload.gestor_email,
            })

        logger.info("Tenant '%s' provisionado por %s", payload.slug, actor.user_id)
        return tenant

    async def update_status(
        self,
        slug: str,
        update: TenantStatusUpdate,
        actor: TenantContext,
    ) -> dict:
        async with get_engine().begin() as conn:
            row = (await conn.execute(
                text("""
                    UPDATE public.tenants
                    SET status = :status, updated_at = now()
                    WHERE slug = :slug
                    RETURNING id, slug, name, status, created_at, updated_at
                """),
                {"slug": slug, "status": update.status},
            )).mappings().first()

            if not row:
                raise LookupError(f"Tenant '{slug}' nao encontrado")

            await self._audit(conn, actor, f"tenant.{update.status}", "tenant", slug, {
                "new_status": update.status,
            })

        return dict(row)

    # ------------------------------------------------------------------
    # Auditoria (privada)
    # ------------------------------------------------------------------

    async def _audit(
        self,
        conn: AsyncSession,
        actor: TenantContext,
        action: str,
        target_type: str,
        target_id: str,
        payload: dict,
    ) -> None:
        await conn.execute(
            text("""
                INSERT INTO public.platform_audit_log
                    (actor_id, actor_email, action, target_type, target_id, payload)
                VALUES
                    (:actor_id, :actor_email, :action, :target_type, :target_id, :payload::jsonb)
            """),
            {
                "actor_id":    actor.user_id,
                "actor_email": actor.email,
                "action":      action,
                "target_type": target_type,
                "target_id":   target_id,
                "payload":     json.dumps(payload),
            },
        )

