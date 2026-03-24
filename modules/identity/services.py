from __future__ import annotations

import re

from .repository import create_pessoa_fisica, get_pessoa_by_cpf
from .schemas import PessoaFisicaIn


def normalize_cpf(cpf: str) -> str:
    cpf_clean = re.sub(r"\D", "", cpf or "")
    if len(cpf_clean) != 11:
        raise ValueError("CPF invalido")
    return cpf_clean


async def find_or_create_by_cpf(payload: PessoaFisicaIn) -> dict:
    cpf_clean = normalize_cpf(payload.cpf)
    existing = await get_pessoa_by_cpf(cpf_clean)
    if existing:
        return existing
    return await create_pessoa_fisica(payload, cpf_clean)
