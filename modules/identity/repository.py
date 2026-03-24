from __future__ import annotations

from uuid import UUID

from sqlalchemy import text

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


async def get_pessoa_by_id(pessoa_id: UUID | str) -> dict | None:
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
