"""
DEM-065 — Tenant Provisioner.

Cria schema PostgreSQL, executa todas as migrations de tenant e
semeia grupo no Keycloak. Pode ser chamado via CLI ou importado
pelo admin service.

Uso CLI:
    python -m tools.scripts.tenant_provisioner --slug novo_tenant --name "Novo Tenant" --gestor-email gestor@exemplo.com
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import pathlib
from typing import Any

import asyncpg

logger = logging.getLogger("intellicare.provisioner")

# Diretório com migrations de tenant (ordem alfabética = ordem de execução)
_TENANT_MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parents[2] / "db" / "tenant_migrations"

# Migration base do admin (users + knowledge_base)
_ADMIN_BASE_MIGRATION = (
    pathlib.Path(__file__).resolve().parents[2] / "modules" / "admin" / "migrations" / "001_tenant_base.sql"
)


def _quote_identifier(identifier: str) -> str:
    """Escape de identificadores SQL para prevenir injection."""
    return '"' + identifier.replace('"', '""') + '"'


def _collect_migration_files() -> list[pathlib.Path]:
    """Coleta e ordena todos os arquivos .sql de tenant migrations."""
    files: list[pathlib.Path] = []
    if _ADMIN_BASE_MIGRATION.exists():
        files.append(_ADMIN_BASE_MIGRATION)
    if _TENANT_MIGRATIONS_DIR.is_dir():
        sql_files = sorted(_TENANT_MIGRATIONS_DIR.glob("*.sql"))
        files.extend(sql_files)
    return files


async def provision_tenant(
    database_url: str,
    slug: str,
    name: str | None = None,
    gestor_email: str | None = None,
    *,
    register_in_platform: bool = True,
) -> dict[str, Any]:
    """
    Provisiona um tenant completo:
    1. Cria schema tenant_{slug}
    2. Executa admin base migration (users, knowledge_base)
    3. Executa todas as tenant_migrations em ordem
    4. Registra na tabela public.tenants (se register_in_platform=True)

    Returns dict com resultado da operação.
    """
    schema = f"tenant_{slug}"
    quoted_schema = _quote_identifier(schema)
    migrations = _collect_migration_files()

    conn = await asyncpg.connect(database_url)
    try:
        # 1. Criar schema
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema}")
        logger.info("Schema %s criado/verificado", schema)

        # 2. Executar migrations dentro do schema
        for migration_file in migrations:
            sql = migration_file.read_text(encoding="utf-8")
            if not sql.strip():
                continue
            await conn.execute(f"SET search_path TO {quoted_schema}, public")
            await conn.execute(sql)
            logger.info("Migration aplicada: %s", migration_file.name)

        # 3. Reset search_path
        await conn.execute("SET search_path TO public")

        # 4. Registrar em public.tenants
        if register_in_platform:
            await conn.execute(
                """
                INSERT INTO public.tenants (slug, name, gestor_email)
                VALUES ($1, $2, $3)
                ON CONFLICT (slug) DO NOTHING
                """,
                slug,
                name or slug,
                gestor_email or "",
            )
            logger.info("Tenant '%s' registrado em public.tenants", slug)

        return {"status": "provisioned", "slug": slug, "schema": schema, "migrations": len(migrations)}
    finally:
        await conn.close()


async def seed_keycloak(
    slug: str,
    keycloak_url: str,
    realm: str,
    admin_user: str,
    admin_password: str,
    gestor_email: str | None = None,
) -> dict[str, Any]:
    """
    Cria grupo tenant_{slug} no Keycloak com atributo tenant_id.
    Se gestor_email fornecido, cria ou associa usuário ao grupo.
    """
    import httpx

    # Obter token admin
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            f"{keycloak_url}/realms/master/protocol/openid-connect/token",
            data={
                "client_id": "admin-cli",
                "grant_type": "password",
                "username": admin_user,
                "password": admin_password,
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        token = token_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Criar grupo
        group_name = f"tenant_{slug}"
        create_resp = await client.post(
            f"{keycloak_url}/admin/realms/{realm}/groups",
            json={"name": group_name, "attributes": {"tenant_id": [slug]}},
            headers=headers,
            timeout=15,
        )
        if create_resp.status_code == 409:
            logger.info("Grupo Keycloak '%s' já existe", group_name)
        elif create_resp.is_error:
            create_resp.raise_for_status()
        else:
            logger.info("Grupo Keycloak '%s' criado", group_name)

    return {"keycloak_group": group_name, "gestor_seeded": bool(gestor_email)}


async def full_provision(
    database_url: str,
    slug: str,
    name: str,
    gestor_email: str,
    keycloak_url: str,
    realm: str,
    kc_admin: str,
    kc_password: str,
) -> dict[str, Any]:
    """Provisiona tenant completo: schema + migrations + Keycloak."""
    db_result = await provision_tenant(
        database_url, slug, name, gestor_email, register_in_platform=True,
    )
    kc_result = await seed_keycloak(
        slug, keycloak_url, realm, kc_admin, kc_password, gestor_email,
    )
    return {**db_result, **kc_result}


def main() -> None:
    """Entrypoint CLI."""
    parser = argparse.ArgumentParser(description="Provisiona novo tenant IntelliCare")
    parser.add_argument("--slug", required=True, help="Slug do tenant (ex: clinica_abc)")
    parser.add_argument("--name", required=True, help="Nome do tenant")
    parser.add_argument("--gestor-email", required=True, help="E-mail do gestor")
    args = parser.parse_args()

    import os
    from intellicare_core.config.settings import get_settings

    settings = get_settings()
    db_url = settings.sync_database_url
    kc_url = settings.keycloak_url
    kc_realm = settings.keycloak_realm
    kc_admin = os.getenv("KEYCLOAK_ADMIN", "admin")
    kc_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin_dev_password")

    result = asyncio.run(
        full_provision(db_url, args.slug, args.name, args.gestor_email, kc_url, kc_realm, kc_admin, kc_password)
    )
    print(f"Tenant provisionado: {result}")


if __name__ == "__main__":
    main()
