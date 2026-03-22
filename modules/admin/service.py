"""Logica de negocio do modulo admin."""
from __future__ import annotations

import json
import logging
import pathlib
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import get_engine
from modules.shared.llm import clear_prompt_cache
from .keycloak_client import KeycloakAdminClient
from .schemas import (
    AdminUserCreate,
    AdminUserUpdate,
    ExpenseCreate,
    ExpenseUpdate,
    InvoiceStatusUpdate,
    ModuleStatusUpdate,
    ServerCreate,
    ServerUpdate,
    TenantConfigItem,
    TenantCreate,
    TenantModuleUpdate,
    PromptTemplateActivateRequest,
    PromptTemplateCreate,
    TenantProvisionRequest,
    TenantStatusUpdate,
    TenantUpdate,
    UserInviteRequest,
)

logger = logging.getLogger("intellicare.admin.service")

_TENANT_MIGRATION = (
    pathlib.Path(__file__).parent / "migrations" / "001_tenant_base.sql"
).read_text(encoding="utf-8")


class TenantService:
    def __init__(self) -> None:
        self._kc = KeycloakAdminClient()

    async def get_dashboard_stats(self) -> dict[str, Any]:
        async with get_engine().connect() as conn:
            row = (
                await conn.execute(text("""
                    SELECT
                        COUNT(*) AS total_tenants,
                        COUNT(*) FILTER (WHERE status = 'active') AS active_tenants,
                        COUNT(*) FILTER (WHERE status = 'suspended') AS suspended_tenants,
                        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS new_last_30d
                    FROM public.tenants
                """))
            ).mappings().first()
            stats = dict(row) if row else {
                "total_tenants": 0,
                "active_tenants": 0,
                "suspended_tenants": 0,
                "new_last_30d": 0,
            }

            revenue = (
                await conn.execute(text("""
                    SELECT COALESCE(SUM(amount_brl), 0)
                    FROM public.invoices
                    WHERE status = 'paid'
                      AND paid_at >= date_trunc('month', NOW())
                """))
            ).scalar_one()
            infra = (
                await conn.execute(text("""
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'active') AS servers_active,
                        COALESCE(SUM(cost_brl) FILTER (WHERE status = 'active'), 0) AS infra_cost_monthly
                    FROM public.servers
                """))
            ).mappings().first()

        stats["monthly_revenue"] = float(revenue or 0) / 100.0
        stats["servers_active"] = int((infra or {}).get("servers_active", 0))
        stats["infra_cost_monthly"] = float((infra or {}).get("infra_cost_monthly", 0) or 0) / 100.0
        return stats

    async def get_audit_log(
        self,
        page: int,
        size: int,
        action: str | None,
        from_date: datetime | None,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: dict[str, Any] = {"limit": size, "offset": (page - 1) * size}
        if action:
            where.append("action = :action")
            params["action"] = action
        if from_date:
            where.append("created_at >= :from_date")
            params["from_date"] = from_date

        where_clause = " AND ".join(where)
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(
                    text(f"""
                        SELECT id, actor_id, actor_email, action, target_type, target_id, payload, created_at
                        FROM public.platform_audit_log
                        WHERE {where_clause}
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    params,
                )
            ).mappings().all()
            total = (
                await conn.execute(
                    text(f"SELECT COUNT(*) FROM public.platform_audit_log WHERE {where_clause}"),
                    {k: v for k, v in params.items() if k not in {'limit', 'offset'}},
                )
            ).scalar_one()
        return {"items": [dict(row) for row in rows], "total": total}

    _TENANT_COLS = "id, slug, name, status, gestor_email, suspended_at, suspended_by, deleted_at, created_at, updated_at"

    async def list_tenants(self, page: int, size: int, actor: TenantContext) -> tuple[list[dict[str, Any]], int]:
        del actor
        async with get_engine().connect() as conn:
            total = (await conn.execute(text("SELECT COUNT(*) FROM public.tenants WHERE deleted_at IS NULL"))).scalar_one()
            rows = (
                await conn.execute(
                    text(f"""
                        SELECT {self._TENANT_COLS}
                        FROM public.tenants
                        WHERE deleted_at IS NULL
                        ORDER BY created_at DESC
                        LIMIT :size OFFSET :offset
                    """),
                    {"size": size, "offset": (page - 1) * size},
                )
            ).mappings().all()
        return [dict(row) for row in rows], total

    async def get_tenant(self, slug: str) -> dict[str, Any] | None:
        async with get_engine().connect() as conn:
            row = (
                await conn.execute(
                    text(f"SELECT {self._TENANT_COLS} FROM public.tenants WHERE slug = :slug AND deleted_at IS NULL"),
                    {"slug": slug},
                )
            ).mappings().first()
        return dict(row) if row else None

    async def get_tenant_users(self, slug: str) -> list[dict[str, Any]]:
        group_id = await self._kc.get_tenant_group_id(slug)
        if not group_id:
            return []
        return await self._kc.get_group_users(group_id)

    async def invite_user(self, slug: str, req: UserInviteRequest, actor: TenantContext) -> dict[str, Any]:
        tenant = await self.get_tenant(slug)
        if not tenant:
            raise ValueError(f"Tenant '{slug}' nao encontrado")
        group_id = await self._kc.get_tenant_group_id(slug)
        if not group_id:
            raise ValueError(f"Grupo Keycloak para tenant '{slug}' nao encontrado")

        result = await self._kc.invite_user(group_id=group_id, email=req.email, name=req.name, role=req.role)
        async with get_engine().begin() as conn:
            await self._audit(conn, actor, "USER_INVITED", "user", req.email, {"tenant": slug, "role": req.role})
        return {"keycloak_id": result, "email": req.email, "role": req.role, "invited": True}

    async def deactivate_user(self, slug: str, user_id: str, actor: TenantContext) -> None:
        await self._kc.deactivate_user(user_id)
        async with get_engine().begin() as conn:
            await self._audit(conn, actor, "USER_DEACTIVATED", "user", user_id, {"tenant": slug})

    async def update_tenant(self, slug: str, payload: TenantUpdate, actor: TenantContext) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.gestor_email is not None:
            updates["gestor_email"] = payload.gestor_email

        if not updates:
            return await self.get_tenant(slug) or {}

        set_clause = ", ".join(f"{key} = :{key}" for key in updates)
        updates["slug"] = slug

        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text(f"""
                        UPDATE public.tenants
                        SET {set_clause}, updated_at = now()
                        WHERE slug = :slug AND deleted_at IS NULL
                        RETURNING {self._TENANT_COLS}
                    """),
                    updates,
                )
            ).mappings().first()
            if not row:
                return {}
            await self._audit(conn, actor, "TENANT_UPDATED", "tenant", slug, payload.model_dump(exclude_none=True))
        return dict(row) if row else {}

    async def delete_tenant(self, slug: str, actor: TenantContext) -> None:
        """Soft-delete: marca deleted_at + status='terminated'. Não dropa schema."""
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text("""
                        UPDATE public.tenants
                        SET status = 'terminated', deleted_at = NOW(), updated_at = NOW()
                        WHERE slug = :slug AND deleted_at IS NULL
                        RETURNING slug
                    """),
                    {"slug": slug},
                )
            ).first()
            if not row:
                raise LookupError(f"Tenant '{slug}' nao encontrado")
            await self._audit(conn, actor, "TENANT_DELETED", "tenant", slug, {"soft_delete": True})

    async def provision_tenant(self, payload: TenantProvisionRequest, actor: TenantContext) -> dict[str, Any]:
        """Provisiona tenant completo: schema + todas as migrations + Keycloak."""
        import os
        from tools.scripts.tenant_provisioner import full_provision
        from intellicare_core.config.settings import get_settings

        settings = get_settings()
        result = await full_provision(
            database_url=settings.sync_database_url,
            slug=payload.slug,
            name=payload.name,
            gestor_email=payload.gestor_email,
            keycloak_url=settings.keycloak_url,
            realm=settings.keycloak_realm,
            kc_admin=os.getenv("KEYCLOAK_ADMIN", "admin"),
            kc_password=os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin_dev_password"),
        )
        async with get_engine().begin() as conn:
            await self._audit(
                conn, actor, "tenant.provision", "tenant", payload.slug,
                {"name": payload.name, "gestor_email": payload.gestor_email},
            )
        tenant = await self.get_tenant(payload.slug)
        return {**(tenant or {}), "provision": result}

    async def get_tenant_config(self, slug: str) -> list[dict[str, str]]:
        """Lista configurações de um tenant."""
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(
                    text("SELECT key, value FROM public.tenant_config WHERE tenant_slug = :slug ORDER BY key"),
                    {"slug": slug},
                )
            ).mappings().all()
        return [dict(row) for row in rows]

    async def set_tenant_config(self, slug: str, key: str, value: str, actor: TenantContext) -> dict[str, str]:
        """Upsert de configuração de tenant."""
        async with get_engine().begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO public.tenant_config (tenant_slug, key, value, updated_at)
                    VALUES (:slug, :key, :value, NOW())
                    ON CONFLICT (tenant_slug, key) DO UPDATE SET value = :value, updated_at = NOW()
                """),
                {"slug": slug, "key": key, "value": value},
            )
            await self._audit(conn, actor, "tenant.config_set", "tenant_config", slug, {"key": key})
        return {"key": key, "value": value}

    async def list_prompt_templates(self) -> list[dict[str, Any]]:
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(
                    text("""
                        SELECT
                            id,
                            prompt_key,
                            version,
                            content,
                            notes,
                            is_active,
                            created_at,
                            created_by,
                            created_by_email,
                            activated_at,
                            activated_by,
                            activated_by_email
                        FROM public.prompt_templates
                        ORDER BY prompt_key ASC, version DESC
                    """)
                )
            ).mappings().all()
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            item = dict(row)
            bucket = grouped.setdefault(
                item["prompt_key"],
                {"prompt_key": item["prompt_key"], "active_version": None, "versions": []},
            )
            if item["is_active"]:
                bucket["active_version"] = item["version"]
            bucket["versions"].append(item)
        return list(grouped.values())

    async def create_prompt_template(self, payload: PromptTemplateCreate, actor: TenantContext) -> dict[str, Any]:
        actor_id = getattr(actor, "user_id", None) or getattr(actor, "sub", None) or "system"
        actor_email = getattr(actor, "email", None)
        async with get_engine().begin() as conn:
            next_version = (
                await conn.execute(
                    text("""
                        SELECT COALESCE(MAX(version), 0) + 1
                        FROM public.prompt_templates
                        WHERE prompt_key = :prompt_key
                    """),
                    {"prompt_key": payload.prompt_key},
                )
            ).scalar_one()
            row = (
                await conn.execute(
                    text("""
                        INSERT INTO public.prompt_templates
                            (prompt_key, version, content, notes, created_by, created_by_email)
                        VALUES
                            (:prompt_key, :version, :content, :notes, :created_by, :created_by_email)
                        RETURNING
                            id, prompt_key, version, content, notes, is_active,
                            created_at, created_by, created_by_email,
                            activated_at, activated_by, activated_by_email
                    """),
                    {
                        "prompt_key": payload.prompt_key,
                        "version": next_version,
                        "content": payload.content,
                        "notes": payload.notes,
                        "created_by": actor_id,
                        "created_by_email": actor_email,
                    },
                )
            ).mappings().first()
            await self._audit(
                conn,
                actor,
                "prompt_template.created",
                "prompt_template",
                payload.prompt_key,
                {"prompt_key": payload.prompt_key, "version": next_version},
            )
        return dict(row) if row else {}

    async def activate_prompt_template(
        self,
        prompt_key: str,
        payload: PromptTemplateActivateRequest,
        actor: TenantContext,
    ) -> dict[str, Any]:
        actor_id = getattr(actor, "user_id", None) or getattr(actor, "sub", None) or "system"
        actor_email = getattr(actor, "email", None)
        async with get_engine().begin() as conn:
            current = (
                await conn.execute(
                    text("""
                        SELECT id
                        FROM public.prompt_templates
                        WHERE prompt_key = :prompt_key
                          AND version = :version
                    """),
                    {"prompt_key": prompt_key, "version": payload.version},
                )
            ).mappings().first()
            if not current:
                raise LookupError(f"Prompt '{prompt_key}' versão {payload.version} não encontrado")

            await conn.execute(
                text("""
                    UPDATE public.prompt_templates
                    SET is_active = false
                    WHERE prompt_key = :prompt_key
                """),
                {"prompt_key": prompt_key},
            )
            await conn.execute(
                text("""
                    UPDATE public.prompt_templates
                    SET is_active = true,
                        activated_at = now(),
                        activated_by = :activated_by,
                        activated_by_email = :activated_by_email
                    WHERE prompt_key = :prompt_key
                      AND version = :version
                """),
                {
                    "prompt_key": prompt_key,
                    "version": payload.version,
                    "activated_by": actor_id,
                    "activated_by_email": actor_email,
                },
            )
            await self._audit(
                conn,
                actor,
                "prompt_template.activated",
                "prompt_template",
                prompt_key,
                {"prompt_key": prompt_key, "version": payload.version},
            )
        clear_prompt_cache(prompt_key)
        return await self.get_prompt_group(prompt_key)

    async def rollback_prompt_template(self, prompt_key: str, actor: TenantContext) -> dict[str, Any]:
        async with get_engine().connect() as conn:
            active_version = (
                await conn.execute(
                    text("""
                        SELECT version
                        FROM public.prompt_templates
                        WHERE prompt_key = :prompt_key
                          AND is_active = true
                    """),
                    {"prompt_key": prompt_key},
                )
            ).scalar_one_or_none()
            if active_version is None:
                raise LookupError(f"Prompt '{prompt_key}' não possui versão ativa")

            previous_version = (
                await conn.execute(
                    text("""
                        SELECT version
                        FROM public.prompt_templates
                        WHERE prompt_key = :prompt_key
                          AND version < :active_version
                        ORDER BY version DESC
                        LIMIT 1
                    """),
                    {"prompt_key": prompt_key, "active_version": active_version},
                )
            ).scalar_one_or_none()
        if previous_version is None:
            raise ValueError(f"Prompt '{prompt_key}' não possui versão anterior para rollback")
        return await self.activate_prompt_template(
            prompt_key,
            PromptTemplateActivateRequest(version=int(previous_version)),
            actor,
        )

    async def get_prompt_group(self, prompt_key: str) -> dict[str, Any]:
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(
                    text("""
                        SELECT
                            id,
                            prompt_key,
                            version,
                            content,
                            notes,
                            is_active,
                            created_at,
                            created_by,
                            created_by_email,
                            activated_at,
                            activated_by,
                            activated_by_email
                        FROM public.prompt_templates
                        WHERE prompt_key = :prompt_key
                        ORDER BY version DESC
                    """),
                    {"prompt_key": prompt_key},
                )
            ).mappings().all()
        if not rows:
            raise LookupError(f"Prompt '{prompt_key}' não encontrado")
        versions = [dict(row) for row in rows]
        active_version = next((item["version"] for item in versions if item["is_active"]), None)
        return {"prompt_key": prompt_key, "active_version": active_version, "versions": versions}

    async def create_tenant(self, payload: TenantCreate, actor: TenantContext) -> dict[str, Any]:
        async with get_engine().begin() as conn:
            existing = (
                await conn.execute(
                    text("SELECT 1 FROM public.tenants WHERE slug = :slug"),
                    {"slug": payload.slug},
                )
            ).first()
            if existing:
                raise ValueError(f"slug '{payload.slug}' ja existe")

            schema = f"tenant_{payload.slug}"
            await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
            await conn.execute(text(f'SET search_path TO "{schema}", public'))
            await conn.execute(text(_TENANT_MIGRATION))
            await conn.execute(text("SET search_path TO public"))
            row = (
                await conn.execute(
                    text(f"""
                        INSERT INTO public.tenants (slug, name, gestor_email)
                        VALUES (:slug, :name, :gestor_email)
                        RETURNING {self._TENANT_COLS}
                    """),
                    {"slug": payload.slug, "name": payload.name, "gestor_email": payload.gestor_email},
                )
            ).mappings().first()
            try:
                await self._kc.create_tenant_group(payload.slug)
            except Exception as exc:
                raise RuntimeError(f"Falha ao criar grupo no Keycloak: {exc}") from exc
            await self._audit(
                conn,
                actor,
                "tenant.create",
                "tenant",
                payload.slug,
                {"name": payload.name, "gestor_email": payload.gestor_email},
            )
        result = dict(row) if row else {}
        result["temporary_password"] = kc_result["temporary_password"]
        return result

    async def update_status(self, slug: str, update: TenantStatusUpdate, actor: TenantContext) -> dict[str, Any]:
        extra_sets = ""
        if update.status == "suspended":
            extra_sets = ", suspended_at = NOW(), suspended_by = :actor_id"
        elif update.status == "active":
            extra_sets = ", suspended_at = NULL, suspended_by = NULL"

        actor_id = getattr(actor, "user_id", None) or "system"
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text(f"""
                        UPDATE public.tenants
                        SET status = :status, updated_at = NOW(){extra_sets}
                        WHERE slug = :slug AND deleted_at IS NULL
                        RETURNING {self._TENANT_COLS}
                    """),
                    {"slug": slug, "status": update.status, "actor_id": actor_id},
                )
            ).mappings().first()
            if not row:
                raise LookupError(f"Tenant '{slug}' nao encontrado")
            await self._audit(conn, actor, f"tenant.{update.status}", "tenant", slug, {"new_status": update.status})
        return dict(row)

    async def list_servers(self) -> list[dict[str, Any]]:
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(
                    text("""
                        SELECT id, name, type, provider, region, hostname, vcpu, ram_gb, disk_gb,
                               cost_brl, status, notes, created_at, updated_at
                        FROM public.servers
                        ORDER BY name
                    """)
                )
            ).mappings().all()
        return [self._map_server(row) for row in rows]

    async def create_server(self, payload: ServerCreate, actor: TenantContext) -> dict[str, Any]:
        values = payload.model_dump()
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text("""
                        INSERT INTO public.servers
                            (name, type, provider, region, hostname, vcpu, ram_gb, disk_gb, cost_brl, status, notes)
                        VALUES
                            (:name, :type, :provider, :region, :hostname, :vcpu, :ram_gb, :disk_gb, :cost_brl, :status, :notes)
                        RETURNING *
                    """),
                    values,
                )
            ).mappings().first()
            await self._audit(conn, actor, "SERVER_CREATED", "server", str(row["id"]), values)
        return self._map_server(row)

    async def update_server(self, server_id: int, payload: ServerUpdate, actor: TenantContext) -> dict[str, Any]:
        updates = payload.model_dump(exclude_none=True)
        if not updates:
            async with get_engine().connect() as conn:
                row = (
                    await conn.execute(text("SELECT * FROM public.servers WHERE id = :id"), {"id": server_id})
                ).mappings().first()
            if not row:
                raise LookupError(f"Servidor '{server_id}' nao encontrado")
            return self._map_server(row)

        set_clause = ", ".join(f"{key} = :{key}" for key in updates)
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text(f"""
                        UPDATE public.servers
                        SET {set_clause}, updated_at = NOW()
                        WHERE id = :id
                        RETURNING *
                    """),
                    {**updates, "id": server_id},
                )
            ).mappings().first()
            if not row:
                raise LookupError(f"Servidor '{server_id}' nao encontrado")
            await self._audit(conn, actor, "SERVER_UPDATED", "server", str(server_id), updates)
        return self._map_server(row)

    async def delete_server(self, server_id: int, actor: TenantContext) -> None:
        async with get_engine().begin() as conn:
            exists = (
                await conn.execute(text("SELECT id FROM public.servers WHERE id = :id"), {"id": server_id})
            ).scalar_one_or_none()
            if not exists:
                raise LookupError(f"Servidor '{server_id}' nao encontrado")
            await conn.execute(text("DELETE FROM public.servers WHERE id = :id"), {"id": server_id})
            await self._audit(conn, actor, "SERVER_DELETED", "server", str(server_id), {})

    async def list_modules(self) -> list[dict[str, Any]]:
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(text("""
                    SELECT
                        pm.id, pm.slug, pm.name, pm.description, pm.version, pm.status,
                        COALESCE(COUNT(tm.tenant_slug) FILTER (WHERE tm.enabled), 0) AS tenant_count
                    FROM public.platform_modules pm
                    LEFT JOIN public.tenant_modules tm ON tm.module_slug = pm.slug
                    GROUP BY pm.id, pm.slug, pm.name, pm.description, pm.version, pm.status
                    ORDER BY pm.name
                """))
            ).mappings().all()
        return [dict(row) for row in rows]

    async def update_module_status(self, slug: str, payload: ModuleStatusUpdate, actor: TenantContext) -> dict[str, Any]:
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text("""
                        UPDATE public.platform_modules
                        SET status = :status, updated_at = NOW()
                        WHERE slug = :slug
                        RETURNING id, slug, name, description, version, status
                    """),
                    {"slug": slug, "status": payload.status},
                )
            ).mappings().first()
            if not row:
                raise LookupError(f"Modulo '{slug}' nao encontrado")
            await self._audit(conn, actor, "MODULE_STATUS_UPDATED", "platform_module", slug, payload.model_dump())
        row_dict = dict(row)
        row_dict["tenant_count"] = await self._count_enabled_tenants(slug)
        return row_dict

    async def list_tenant_modules(self, tenant_slug: str) -> list[dict[str, Any]]:
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(
                    text("""
                        SELECT
                            :tenant_slug AS tenant_slug,
                            pm.slug AS module_slug,
                            pm.name,
                            pm.description,
                            pm.version,
                            pm.status,
                            COALESCE(tm.enabled, false) AS enabled,
                            tm.enabled_at
                        FROM public.platform_modules pm
                        LEFT JOIN public.tenant_modules tm
                          ON tm.module_slug = pm.slug
                         AND tm.tenant_slug = :tenant_slug
                        ORDER BY pm.name
                    """),
                    {"tenant_slug": tenant_slug},
                )
            ).mappings().all()
        return [dict(row) for row in rows]

    async def update_tenant_module(
        self,
        tenant_slug: str,
        module_slug: str,
        payload: TenantModuleUpdate,
        actor: TenantContext,
    ) -> dict[str, Any]:
        async with get_engine().begin() as conn:
            module = (
                await conn.execute(
                    text("SELECT slug, status FROM public.platform_modules WHERE slug = :slug"),
                    {"slug": module_slug},
                )
            ).mappings().first()
            if not module:
                raise LookupError(f"Modulo '{module_slug}' nao encontrado")
            if payload.enabled and module["status"] == "dev":
                raise ValueError(f"Modulo '{module_slug}' em desenvolvimento nao pode ser habilitado")

            await conn.execute(
                text("""
                    INSERT INTO public.tenant_modules (tenant_slug, module_slug, enabled, enabled_at)
                    VALUES (:tenant_slug, :module_slug, :enabled, NOW())
                    ON CONFLICT (tenant_slug, module_slug)
                    DO UPDATE SET enabled = EXCLUDED.enabled, enabled_at = NOW()
                """),
                {"tenant_slug": tenant_slug, "module_slug": module_slug, "enabled": payload.enabled},
            )
            row = (
                await conn.execute(
                    text("""
                        SELECT
                            :tenant_slug AS tenant_slug,
                            pm.slug AS module_slug,
                            pm.name,
                            pm.description,
                            pm.version,
                            pm.status,
                            tm.enabled,
                            tm.enabled_at
                        FROM public.platform_modules pm
                        JOIN public.tenant_modules tm
                          ON tm.module_slug = pm.slug
                         AND tm.tenant_slug = :tenant_slug
                        WHERE pm.slug = :module_slug
                    """),
                    {"tenant_slug": tenant_slug, "module_slug": module_slug},
                )
            ).mappings().first()
            await self._audit(
                conn,
                actor,
                "TENANT_MODULE_UPDATED",
                "tenant_module",
                f"{tenant_slug}:{module_slug}",
                payload.model_dump(),
            )
        return dict(row) if row else {}

    async def get_financeiro_dashboard(self) -> dict[str, Any]:
        async with get_engine().connect() as conn:
            receita_mes = (
                await conn.execute(text("""
                    SELECT COALESCE(SUM(amount_brl), 0)
                    FROM public.invoices
                    WHERE status = 'paid'
                      AND paid_at >= date_trunc('month', NOW())
                """))
            ).scalar_one()
            despesas_avulsas = (
                await conn.execute(text("""
                    SELECT COALESCE(SUM(amount_brl), 0)
                    FROM public.expenses
                    WHERE expense_date >= date_trunc('month', CURRENT_DATE)
                """))
            ).scalar_one()
            custo_servidores = (
                await conn.execute(text("""
                    SELECT COALESCE(SUM(cost_brl), 0)
                    FROM public.servers
                    WHERE status = 'active'
                """))
            ).scalar_one()
            inadimplencia = (
                await conn.execute(text("""
                    SELECT COALESCE(SUM(amount_brl), 0)
                    FROM public.invoices
                    WHERE status = 'overdue'
                       OR (status = 'pending' AND due_date < CURRENT_DATE)
                """))
            ).scalar_one()
            historico_rows = (
                await conn.execute(text("""
                    WITH months AS (
                        SELECT generate_series(
                            date_trunc('month', CURRENT_DATE) - INTERVAL '5 months',
                            date_trunc('month', CURRENT_DATE),
                            INTERVAL '1 month'
                        ) AS month_start
                    ),
                    revenue AS (
                        SELECT date_trunc('month', paid_at) AS month_start, SUM(amount_brl) AS total
                        FROM public.invoices
                        WHERE status = 'paid' AND paid_at >= date_trunc('month', CURRENT_DATE) - INTERVAL '5 months'
                        GROUP BY 1
                    ),
                    expenses AS (
                        SELECT date_trunc('month', expense_date::timestamp) AS month_start, SUM(amount_brl) AS total
                        FROM public.expenses
                        WHERE expense_date >= date_trunc('month', CURRENT_DATE) - INTERVAL '5 months'
                        GROUP BY 1
                    ),
                    infra AS (
                        SELECT COALESCE(SUM(cost_brl), 0) AS total
                        FROM public.servers
                        WHERE status = 'active'
                    )
                    SELECT
                        to_char(months.month_start, 'YYYY-MM') AS mes,
                        COALESCE(revenue.total, 0) AS receita_brl,
                        COALESCE(expenses.total, 0) + infra.total AS despesa_brl
                    FROM months
                    LEFT JOIN revenue ON revenue.month_start = months.month_start
                    LEFT JOIN expenses ON expenses.month_start = months.month_start
                    CROSS JOIN infra
                    ORDER BY months.month_start
                """))
            ).mappings().all()

        despesa_mes_total = int(despesas_avulsas or 0) + int(custo_servidores or 0)
        return {
            "receita_mes": float(receita_mes or 0) / 100.0,
            "despesa_mes": float(despesa_mes_total) / 100.0,
            "resultado_mes": float((receita_mes or 0) - despesa_mes_total) / 100.0,
            "inadimplencia": float(inadimplencia or 0) / 100.0,
            "historico": [
                {
                    "mes": row["mes"],
                    "receita": float(row["receita_brl"] or 0) / 100.0,
                    "despesa": float(row["despesa_brl"] or 0) / 100.0,
                    "resultado": float((row["receita_brl"] or 0) - (row["despesa_brl"] or 0)) / 100.0,
                }
                for row in historico_rows
            ],
        }

    async def list_invoices(
        self,
        page: int,
        size: int,
        status: str | None,
        tenant_slug: str | None,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: dict[str, Any] = {"limit": size, "offset": (page - 1) * size}
        if status:
            where.append("i.status = :status")
            params["status"] = status
        if tenant_slug:
            where.append("i.tenant_slug = :tenant_slug")
            params["tenant_slug"] = tenant_slug
        where_clause = " AND ".join(where)

        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(
                    text(f"""
                        SELECT i.*
                        FROM public.invoices i
                        WHERE {where_clause}
                        ORDER BY i.due_date DESC, i.created_at DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    params,
                )
            ).mappings().all()
            total = (
                await conn.execute(
                    text(f"SELECT COUNT(*) FROM public.invoices i WHERE {where_clause}"),
                    {k: v for k, v in params.items() if k not in {'limit', 'offset'}},
                )
            ).scalar_one()
        return {
            "items": [self._map_invoice(row) for row in rows],
            "total": total,
            "page": page,
            "size": size,
        }

    async def update_invoice_status(
        self,
        invoice_id: str,
        payload: InvoiceStatusUpdate,
        actor: TenantContext,
    ) -> dict[str, Any]:
        paid_at = payload.paid_at
        if payload.status == "paid" and paid_at is None:
            paid_at = datetime.now(UTC)
        if payload.status != "paid":
            paid_at = None
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text("""
                        UPDATE public.invoices
                        SET status = :status, paid_at = :paid_at
                        WHERE id = :id
                        RETURNING *
                    """),
                    {"id": invoice_id, "status": payload.status, "paid_at": paid_at},
                )
            ).mappings().first()
            if not row:
                raise LookupError(f"Fatura '{invoice_id}' nao encontrada")
            audit_payload = payload.model_dump()
            audit_payload["paid_at"] = paid_at.isoformat() if paid_at else None
            await self._audit(conn, actor, "INVOICE_STATUS_UPDATED", "invoice", invoice_id, audit_payload)
        return self._map_invoice(row)

    async def list_expenses(self, page: int, size: int) -> dict[str, Any]:
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(
                    text("""
                        SELECT id, category, description, amount_brl, expense_date, tenant_slug, created_at
                        FROM public.expenses
                        ORDER BY expense_date DESC, id DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    {"limit": size, "offset": (page - 1) * size},
                )
            ).mappings().all()
            total = (await conn.execute(text("SELECT COUNT(*) FROM public.expenses"))).scalar_one()
        return {
            "items": [self._map_expense(row) for row in rows],
            "total": total,
            "page": page,
            "size": size,
        }

    async def create_expense(self, payload: ExpenseCreate, actor: TenantContext) -> dict[str, Any]:
        values = payload.model_dump()
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text("""
                        INSERT INTO public.expenses (category, description, amount_brl, expense_date, tenant_slug)
                        VALUES (:category, :description, :amount_brl, :expense_date, :tenant_slug)
                        RETURNING id, category, description, amount_brl, expense_date, tenant_slug, created_at
                    """),
                    values,
                )
            ).mappings().first()
            await self._audit(conn, actor, "EXPENSE_CREATED", "expense", str(row["id"]), values)
        return self._map_expense(row)

    async def update_expense(self, expense_id: int, payload: ExpenseUpdate, actor: TenantContext) -> dict[str, Any]:
        updates = payload.model_dump(exclude_none=True)
        if not updates:
            async with get_engine().connect() as conn:
                row = (
                    await conn.execute(
                        text("""
                            SELECT id, category, description, amount_brl, expense_date, tenant_slug, created_at
                            FROM public.expenses
                            WHERE id = :id
                        """),
                        {"id": expense_id},
                    )
                ).mappings().first()
            if not row:
                raise LookupError(f"Despesa '{expense_id}' nao encontrada")
            return self._map_expense(row)

        set_clause = ", ".join(f"{key} = :{key}" for key in updates)
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text(f"""
                        UPDATE public.expenses
                        SET {set_clause}
                        WHERE id = :id
                        RETURNING id, category, description, amount_brl, expense_date, tenant_slug, created_at
                    """),
                    {**updates, "id": expense_id},
                )
            ).mappings().first()
            if not row:
                raise LookupError(f"Despesa '{expense_id}' nao encontrada")
            await self._audit(conn, actor, "EXPENSE_UPDATED", "expense", str(expense_id), updates)
        return self._map_expense(row)

    async def delete_expense(self, expense_id: int, actor: TenantContext) -> None:
        async with get_engine().begin() as conn:
            exists = (
                await conn.execute(text("SELECT id FROM public.expenses WHERE id = :id"), {"id": expense_id})
            ).scalar_one_or_none()
            if not exists:
                raise LookupError(f"Despesa '{expense_id}' nao encontrada")
            await conn.execute(text("DELETE FROM public.expenses WHERE id = :id"), {"id": expense_id})
            await self._audit(conn, actor, "EXPENSE_DELETED", "expense", str(expense_id), {})

    async def list_admin_users(self) -> list[dict[str, Any]]:
        async with get_engine().connect() as conn:
            rows = (
                await conn.execute(text("""
                    SELECT id, keycloak_id, email, name, role, status, last_login_at, created_at
                    FROM public.admin_users
                    ORDER BY created_at DESC
                """))
            ).mappings().all()
        return [dict(row) for row in rows]

    async def create_admin_user(self, payload: AdminUserCreate, actor: TenantContext) -> dict[str, Any]:
        kc_result = await self._kc.create_admin_user(payload.email, payload.name, enabled=payload.status == "active")
        async with get_engine().begin() as conn:
            row = (
                await conn.execute(
                    text("""
                        INSERT INTO public.admin_users (keycloak_id, email, name, role, status)
                        VALUES (:keycloak_id, :email, :name, :role, :status)
                        ON CONFLICT (email)
                        DO UPDATE SET
                            keycloak_id = EXCLUDED.keycloak_id,
                            name = EXCLUDED.name,
                            role = EXCLUDED.role,
                            status = EXCLUDED.status
                        RETURNING id, keycloak_id, email, name, role, status, last_login_at, created_at
                    """),
                    {
                        "keycloak_id": kc_result["id"],
                        "email": payload.email,
                        "name": payload.name,
                        "role": payload.role,
                        "status": payload.status,
                    },
                )
            ).mappings().first()
            await self._audit(
                conn,
                actor,
                "ADMIN_USER_CREATED",
                "admin_user",
                payload.email,
                {**payload.model_dump(), "temporary_password": kc_result["temporary_password"]},
            )
        return dict(row) if row else {}

    async def update_admin_user(self, user_id: int, payload: AdminUserUpdate, actor: TenantContext) -> dict[str, Any]:
        updates = payload.model_dump(exclude_none=True)
        async with get_engine().begin() as conn:
            current = (
                await conn.execute(
                    text("""
                        SELECT id, keycloak_id, email, name, role, status, last_login_at, created_at
                        FROM public.admin_users
                        WHERE id = :id
                    """),
                    {"id": user_id},
                )
            ).mappings().first()
            if not current:
                raise LookupError(f"Usuario admin '{user_id}' nao encontrado")

            if current["keycloak_id"]:
                await self._kc.update_admin_user(
                    current["keycloak_id"],
                    name=updates.get("name"),
                    enabled=(updates.get("status", current["status"]) == "active"),
                )

            set_clause = ", ".join(f"{key} = :{key}" for key in updates) or "name = name"
            row = (
                await conn.execute(
                    text(f"""
                        UPDATE public.admin_users
                        SET {set_clause}
                        WHERE id = :id
                        RETURNING id, keycloak_id, email, name, role, status, last_login_at, created_at
                    """),
                    {**updates, "id": user_id},
                )
            ).mappings().first()
            await self._audit(conn, actor, "ADMIN_USER_UPDATED", "admin_user", str(user_id), updates)
        return dict(row) if row else {}

    async def delete_admin_user(self, user_id: int, actor: TenantContext) -> None:
        async with get_engine().begin() as conn:
            current = (
                await conn.execute(
                    text("SELECT id, keycloak_id, email FROM public.admin_users WHERE id = :id"),
                    {"id": user_id},
                )
            ).mappings().first()
            if not current:
                raise LookupError(f"Usuario admin '{user_id}' nao encontrado")
            if current["keycloak_id"]:
                await self._kc.delete_user(current["keycloak_id"])
            await conn.execute(text("DELETE FROM public.admin_users WHERE id = :id"), {"id": user_id})
            await self._audit(conn, actor, "ADMIN_USER_DELETED", "admin_user", str(user_id), {"email": current["email"]})

    async def _count_enabled_tenants(self, module_slug: str) -> int:
        async with get_engine().connect() as conn:
            total = (
                await conn.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM public.tenant_modules
                        WHERE module_slug = :module_slug
                          AND enabled = true
                    """),
                    {"module_slug": module_slug},
                )
            ).scalar_one()
        return int(total)

    async def _audit(
        self,
        conn: Any,
        actor: TenantContext,
        action: str,
        target_type: str,
        target_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        actor_id = getattr(actor, "user_id", None) or getattr(actor, "sub", None) or "system"
        actor_email = getattr(actor, "email", None)
        await conn.execute(
            text("""
                INSERT INTO public.platform_audit_log
                    (actor_id, actor_email, action, target_type, target_id, payload)
                VALUES
                    (:actor_id, :actor_email, :action, :target_type, :target_id, CAST(:payload AS jsonb))
            """),
            {
                "actor_id": actor_id,
                "actor_email": actor_email,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "payload": json.dumps(payload, default=self._json_default),
            },
        )

    def _map_server(self, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "provider": row["provider"],
            "region": row["region"],
            "hostname": row["hostname"],
            "vcpu": row["vcpu"],
            "ram_gb": row["ram_gb"],
            "disk_gb": row["disk_gb"],
            "cost_brl": row["cost_brl"],
            "cost_brl_display": float(row["cost_brl"] or 0) / 100.0,
            "status": row["status"],
            "notes": row["notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _map_invoice(self, row: Any) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "contract_id": str(row["contract_id"]),
            "tenant_slug": row["tenant_slug"],
            "amount_brl": row["amount_brl"],
            "amount_brl_display": float(row["amount_brl"] or 0) / 100.0,
            "due_date": row["due_date"],
            "paid_at": row["paid_at"],
            "status": row["status"],
            "period_start": row["period_start"],
            "period_end": row["period_end"],
            "created_at": row["created_at"],
        }

    def _map_expense(self, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "category": row["category"],
            "description": row["description"],
            "amount_brl": row["amount_brl"],
            "amount_brl_display": float(row["amount_brl"] or 0) / 100.0,
            "expense_date": row["expense_date"],
            "tenant_slug": row["tenant_slug"],
            "created_at": row["created_at"],
        }

    def _json_default(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
