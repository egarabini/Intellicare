from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class PessoaFisicaIn(BaseModel):
    nome_completo: str = Field(min_length=1, max_length=255)
    cpf: str = Field(min_length=11, max_length=20)
    data_nascimento: date | None = None
    genero: str | None = None


class PessoaOut(BaseModel):
    id: UUID
    tipo: str
    nome_completo: str
    cpf: str | None
    data_nascimento: date | None = None
    genero: str | None = None

