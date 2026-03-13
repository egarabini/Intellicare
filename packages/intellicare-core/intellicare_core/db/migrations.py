"""
Helpers para criacao e migracao de schemas por tenant.
"""

from __future__ import annotations

import asyncpg

from intellicare_core.config.settings import get_settings


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


async def provision_tenant_schema(slug: str) -> None:
    settings = get_settings()
    schema = f"tenant_{slug}"
    quoted_schema = _quote_identifier(schema)

    conn = await asyncpg.connect(settings.sync_database_url)
    try:
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema}")
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quoted_schema}.knowledge_base (
                id          SERIAL PRIMARY KEY,
                title       TEXT NOT NULL,
                content     TEXT NOT NULL,
                source_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL DEFAULT 0,
                embedding   vector(768),
                metadata    JSONB DEFAULT '{{}}',
                created_at  TIMESTAMPTZ DEFAULT now(),
                updated_at  TIMESTAMPTZ DEFAULT now(),
                UNIQUE (source_path, chunk_index)
            )
            """
        )
    finally:
        await conn.close()


async def drop_tenant_schema(slug: str) -> None:
    settings = get_settings()
    schema = _quote_identifier(f"tenant_{slug}")
    conn = await asyncpg.connect(settings.sync_database_url)
    try:
        await conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    finally:
        await conn.close()
