#!/usr/bin/env python3
"""
reset_demo.py - Remove os dados de demonstracao do IntelliCare V3.
Mantem schemas e tabelas, mas limpa o seed de homologacao.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages" / "intellicare-core"))

from intellicare_core.config.settings import get_settings
from intellicare_core.db.session import get_engine
from tools.scripts.setup_keycloak import KeycloakAdmin, delete_demo_users

settings = get_settings()
DEMO_SLUGS = ["clinica_alfa", "hospital_beta", "consultorio_gamma"]
DEMO_PLAN_NAMES = ["Basic", "Pro", "Enterprise"]
DOCS_ROOT = ROOT / "tools" / "data" / "docs"


async def public_table_exists(session: AsyncSession, table: str) -> bool:
    row = await session.execute(
        text(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = :table
            """
        ),
        {"table": table},
    )
    return bool(row.scalar_one_or_none())


async def reset_tenant_schema(session: AsyncSession, slug: str) -> None:
    schema = f"tenant_{slug}"
    schema_exists = (
        await session.execute(
            text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema"),
            {"schema": schema},
        )
    ).scalar_one_or_none()
    if not schema_exists:
        return
    for table in [
        "program_enrollments",
        "health_programs",
        "encounter_notes",
        "encounters",
        "patients",
        "slm_query_log",
        "unit_profile",
        "ingest_log",
        "knowledge_base",
        "users",
    ]:
        table_exists = (
            await session.execute(
                text(
                    """
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                      AND table_name = :table
                    """
                ),
                {"schema": schema, "table": table},
            )
        ).scalar_one_or_none()
        if table_exists:
            await session.execute(text(f'DELETE FROM "{schema}".{table}'))
    await session.commit()


async def reset_platform(session: AsyncSession, slugs: list[str]) -> None:
    if await public_table_exists(session, "invoices"):
        await session.execute(
            text("DELETE FROM public.invoices WHERE tenant_slug = ANY(:slugs)"),
            {"slugs": slugs},
        )
    if await public_table_exists(session, "contracts"):
        await session.execute(
            text("DELETE FROM public.contracts WHERE tenant_slug = ANY(:slugs)"),
            {"slugs": slugs},
        )
    if await public_table_exists(session, "platform_audit_log"):
        await session.execute(
            text("DELETE FROM public.platform_audit_log WHERE target_id = ANY(:slugs)"),
            {"slugs": slugs},
        )
    if await public_table_exists(session, "tenants"):
        await session.execute(
            text("DELETE FROM public.tenants WHERE slug = ANY(:slugs)"),
            {"slugs": slugs},
        )
    if await public_table_exists(session, "plans") and await public_table_exists(session, "contracts"):
        await session.execute(
            text(
                """
                DELETE FROM public.plans p
                WHERE p.name = ANY(:plan_names)
                  AND NOT EXISTS (SELECT 1 FROM public.contracts c WHERE c.plan_id = p.id)
                """
            ),
            {"plan_names": DEMO_PLAN_NAMES},
        )
    await session.commit()


async def reset_keycloak(slugs: list[str]) -> None:
    kc = KeycloakAdmin(
        settings.keycloak_url,
        os.getenv("KEYCLOAK_ADMIN", "admin"),
        os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin_dev_password"),
    )
    for slug in slugs:
        delete_demo_users(kc, tenant_filter=slug)


def reset_docs(slugs: list[str]) -> None:
    for slug in slugs:
        target = DOCS_ROOT / slug
        if target.exists():
            shutil.rmtree(target)


async def main(args: argparse.Namespace) -> None:
    slugs = [args.tenant] if args.tenant else DEMO_SLUGS
    engine = get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        print("\n=== IntelliCare V3 - Reset de Demonstracao ===\n")
        for slug in slugs:
            print(f"-> limpando tenant_{slug}")
            await reset_tenant_schema(session, slug)
        print("-> limpando dados de plataforma")
        await reset_platform(session, slugs)

    print("-> limpando Keycloak")
    await reset_keycloak(slugs)
    print("-> limpando diretorios de documentos")
    reset_docs(slugs)
    print("\nReset concluido.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset de dados de demonstracao IntelliCare")
    parser.add_argument("--tenant", help="Limpa apenas este tenant de demonstracao")
    asyncio.run(main(parser.parse_args()))
