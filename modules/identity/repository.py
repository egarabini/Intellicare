from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from intellicare_core.db.session import get_engine
from .schemas import PessoaFisicaIn


async def get_pessoa_by_cpf(cpf: str) -> dict | None:
    async with get_engine().connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT
                    p.id,
                    p.tipo,
                    pf.nome_completo,
                    pf.cpf,
                    pf.data_nascimento,
                    pf.genero
                FROM platform.pessoa p
                JOIN platform.pessoa_fisica pf
                  ON pf.pessoa_id = p.id
                WHERE pf.cpf = :cpf
                LIMIT 1
                """
            ),
            {"cpf": cpf},
        )
        row = result.mappings().first()
    return dict(row) if row else None


async def get_pessoa_by_id(pessoa_id: uuid.UUID | str) -> dict | None:
    async with get_engine().connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT
                    p.id,
                    p.tipo,
                    pf.nome_completo,
                    pf.cpf,
                    pf.data_nascimento,
                    pf.genero
                FROM platform.pessoa p
                LEFT JOIN platform.pessoa_fisica pf
                  ON pf.pessoa_id = p.id
                WHERE p.id = :pessoa_id
                LIMIT 1
                """
            ),
            {"pessoa_id": str(pessoa_id)},
        )
        row = result.mappings().first()
    return dict(row) if row else None


async def create_pessoa_fisica(payload: PessoaFisicaIn, cpf_clean: str) -> dict:
    async with get_engine().begin() as conn:
        pessoa_id = (
            await conn.execute(
                text(
                    """
                    INSERT INTO platform.pessoa (tipo)
                    VALUES ('FISICA')
                    RETURNING id
                    """
                )
            )
        ).scalar_one()

        await conn.execute(
            text(
                """
                INSERT INTO platform.pessoa_fisica (
                    pessoa_id,
                    nome_completo,
                    cpf,
                    data_nascimento,
                    genero
                )
                VALUES (
                    :pessoa_id,
                    :nome_completo,
                    :cpf,
                    :data_nascimento,
                    :genero
                )
                """
            ),
            {
                "pessoa_id": pessoa_id,
                "nome_completo": payload.nome_completo,
                "cpf": cpf_clean,
                "data_nascimento": payload.data_nascimento,
                "genero": payload.genero,
            },
        )

        result = await conn.execute(
            text(
                """
                SELECT
                    p.id,
                    p.tipo,
                    pf.nome_completo,
                    pf.cpf,
                    pf.data_nascimento,
                    pf.genero
                FROM platform.pessoa p
                JOIN platform.pessoa_fisica pf
                  ON pf.pessoa_id = p.id
                WHERE p.id = :pessoa_id
                """
            ),
            {"pessoa_id": pessoa_id},
        )
        row = result.mappings().first()
    return dict(row)


async def register_tenant_link(
    db: AsyncSession,
    pessoa_id: uuid.UUID,
    tenant_slug: str,
) -> None:
    """
    Upsert: se o vínculo já existe (mesmo pessoa_id + tenant_slug),
    apenas reativa (ativo=True). Não duplica.
    """
    await db.execute(
        text(
            """
            INSERT INTO platform.pessoa_estabelecimento (pessoa_id, tenant_slug, ativo)
            VALUES (:pessoa_id, :tenant_slug, TRUE)
            ON CONFLICT (pessoa_id, tenant_slug)
            DO UPDATE SET ativo = TRUE, data_desvinculo = NULL
            """
        ),
        {"pessoa_id": str(pessoa_id), "tenant_slug": tenant_slug},
    )


async def list_tenants() -> list[dict]:
    async with get_engine().connect() as conn:
        rows = (
            await conn.execute(
                text(
                    """
                    SELECT slug, status
                    FROM public.tenants
                    WHERE status = 'active'
                    ORDER BY slug
                    """
                )
            )
        ).mappings().all()
    return [dict(row) for row in rows]


async def count_pessoas_fisicas() -> int:
    async with get_engine().connect() as conn:
        total = await conn.execute(text("SELECT COUNT(*) FROM platform.pessoa_fisica"))
    return int(total.scalar_one() or 0)


async def table_exists(schema: str, table_name: str) -> bool:
    async with get_engine().connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                      AND table_name = :table_name
                )
                """
            ),
            {"schema": schema, "table_name": table_name},
        )
    return bool(result.scalar_one())


async def column_exists(schema: str, table_name: str, column_name: str) -> bool:
    async with get_engine().connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = :schema
                      AND table_name = :table_name
                      AND column_name = :column_name
                )
                """
            ),
            {"schema": schema, "table_name": table_name, "column_name": column_name},
        )
    return bool(result.scalar_one())


async def first_existing_column(schema: str, table_name: str, candidates: list[str]) -> str | None:
    for column_name in candidates:
        if await column_exists(schema, table_name, column_name):
            return column_name
    return None
