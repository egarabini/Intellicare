"""GestorService — logica de negocio do modulo gestor."""
from __future__ import annotations

import logging

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session
from modules.admin.keycloak_client import KeycloakAdminClient

logger = logging.getLogger("intellicare.gestor.service")


class GestorService:
    def __init__(self) -> None:
        self._kc = KeycloakAdminClient()

    async def get_profile(self, ctx: TenantContext) -> dict | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(text("SELECT * FROM unit_profile LIMIT 1"))
            ).mappings().first()
        return dict(row) if row else None

    async def upsert_profile(self, ctx: TenantContext, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            exists = (
                await db.execute(text("SELECT id FROM unit_profile LIMIT 1"))
            ).first()
            if exists:
                row = (
                    await db.execute(
                        text(
                            "UPDATE unit_profile SET name=:name, address=:address, city=:city, "
                            "state=:state, unit_type=:unit_type, phone=:phone, email=:email, "
                            "updated_at=now() RETURNING *"
                        ),
                        data,
                    )
                ).mappings().first()
            else:
                row = (
                    await db.execute(
                        text(
                            "INSERT INTO unit_profile (name, address, city, state, unit_type, phone, email) "
                            "VALUES (:name, :address, :city, :state, :unit_type, :phone, :email) RETURNING *"
                        ),
                        data,
                    )
                ).mappings().first()
        return dict(row)

    async def list_documents(self, ctx: TenantContext) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        "SELECT source_path, COUNT(*) AS chunk_count, "
                        "MAX(created_at) AS last_ingested_at "
                        "FROM knowledge_base GROUP BY source_path "
                        "ORDER BY last_ingested_at DESC"
                    )
                )
            ).mappings().all()
        return [dict(r) for r in rows]

    async def usage_report(self, ctx: TenantContext, days: int = 30) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("""
                        SELECT COUNT(*) AS total_queries,
                               COALESCE(AVG(latency_ms), 0) AS avg_latency_ms,
                               MIN(created_at) AS period_start,
                               MAX(created_at) AS period_end
                        FROM slm_query_log
                        WHERE created_at >= now() - make_interval(days => :days)
                    """),
                    {"days": days},
                )
            ).mappings().first()
            top = (
                await db.execute(
                    text("""
                        SELECT query_text FROM slm_query_log
                        WHERE created_at >= now() - make_interval(days => :days)
                        GROUP BY query_text ORDER BY COUNT(*) DESC LIMIT 5
                    """),
                    {"days": days},
                )
            ).fetchall()
        return {**dict(row), "top_queries": [r[0] for r in top]}
