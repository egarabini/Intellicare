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
from .schemas import (
    TenantCreate,
    TenantStatusUpdate,
    TenantUpdateRequest,
    UserInviteRequest,
)

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

    async def get_dashboard_stats(self) -> dict:
        async with get_engine().connect() as conn:
            row = (await conn.execute(text("""
                SELECT
                    COUNT(*)                                    AS total_tenants,
                    COUNT(*) FILTER (WHERE status = 'active')  AS active_tenants,
                    COUNT(*) FILTER (WHERE status = 'suspended') AS suspended_tenants,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS new_last_30d
                FROM public.tenants
            """))).first()
            if not row:
                stats = {
                    "total_tenants": 0, "active_tenants": 0, "suspended_tenants": 0, "new_last_30d": 0, "monthly_revenue": 0.0
                }
                return stats
            stats = dict(row._mapping)

            # Receita mensal estimada (soma de faturas do mes corrente)
            rev = (await conn.execute(text("""
                SELECT COALESCE(SUM(i.amount), 0) AS monthly_revenue
                FROM public.invoices i
                WHERE i.status = 'paid'
                  AND i.paid_at >= date_trunc('month', NOW())
            """))).scalar_one()
            stats["monthly_revenue"] = float(rev)
        return stats

    async def get_audit_log(
        self, page: int, size: int,
        action: str | None, from_date: datetime | None
    ) -> dict:
        where = ["1=1"]
        params: dict = {"limit": size, "offset": (page - 1) * size}
        if action:
            where.append("action = :action")
            params["action"] = action
        if from_date:
            where.append("created_at >= :from_date")
            params["from_date"] = from_date

        where_clause = " AND ".join(where)
        async with get_engine().connect() as conn:
            rows = (await conn.execute(
                text(f"""
                    SELECT id, actor_id, actor_email, action, target_type,
                           target_id, payload, created_at
                    FROM public.platform_audit_log
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """), params
            )).mappings().all()
            
            count = (await conn.execute(
                text(f"SELECT COUNT(*) FROM public.platform_audit_log WHERE {where_clause}"),
                {k: v for k, v in params.items() if k not in ("limit", "offset")},
            )).scalar_one()

        return {
            "items": [dict(r) for r in rows],
            "total": count,
        }

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

    async def invite_user(self, slug: str, req: UserInviteRequest, actor: TenantContext) -> dict:
        tenant = await self.get_tenant(slug)
        if not tenant:
            raise ValueError(f"Tenant '{slug}' nao encontrado")
        group_id = await self._kc.get_tenant_group_id(slug)
        if not group_id:
            raise ValueError(f"Grupo Keycloak para tenant '{slug}' nao encontrado")
            
        result = await self._kc.invite_user(
            group_id=group_id,
            email=req.email,
            name=req.name,
            role=req.role,
        )
        async with get_engine().begin() as conn:
            await self._audit(
                conn, actor, action="USER_INVITED",
                target_type="user", target_id=req.email,
                payload={"tenant": slug, "role": req.role},
            )
        return {
            "keycloak_id": result,
            "email": req.email,
            "role": req.role,
            "invited": True,
        }

    async def deactivate_user(self, slug: str, user_id: str, actor: TenantContext) -> None:
        await self._kc.deactivate_user(user_id)
        async with get_engine().begin() as conn:
            await self._audit(
                conn, actor, action="USER_DEACTIVATED",
                target_type="user", target_id=user_id,
                payload={"tenant": slug},
            )

    async def update_tenant(self, slug: str, req: TenantUpdateRequest, actor: TenantContext) -> dict:
        async with get_engine().begin() as conn:
            await conn.execute(
                text("UPDATE public.tenants SET name=:name, updated_at=NOW() WHERE slug=:slug"),
                {"name": req.name, "slug": slug},
            )
            await self._audit(
                conn, actor, action="TENANT_UPDATED",
                target_type="tenant", target_id=slug,
                payload={"name": req.name},
            )
        tenant = await self.get_tenant(slug)
        if not tenant:
            raise ValueError(f"Tenant '{slug}' nao encontrado")
        return tenant

    async def delete_tenant(self, slug: str, actor: TenantContext) -> None:
        async with get_engine().begin() as conn:
            schema = f"tenant_{slug.replace('-', '_')}"
            # 1. Drop schema com todos os dados
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
            # 2. Soft delete na tabela de tenants
            await conn.execute(
                text("UPDATE public.tenants SET status='terminated', updated_at=NOW() WHERE slug=:slug"),
                {"slug": slug},
            )
            await self._audit(
                conn, actor, action="TENANT_DELETED",
                target_type="tenant", target_id=slug, payload={},
            )
            
        # 3. Remover grupo do Keycloak
        group_id = await self._kc.get_tenant_group_id(slug)
        if group_id:
            await self._kc.delete_group(group_id)



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

