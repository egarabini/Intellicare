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


class IdentityReconcileError(BaseModel):
    tenant_slug: str
    scope: str
    record_id: str
    error: str


class IdentityReconcileResult(BaseModel):
    processed: int = 0
    linked: int = 0
    skipped: int = 0
    errors: list[IdentityReconcileError] = Field(default_factory=list)


class IdentityTenantStats(BaseModel):
    slug: str
    status: str
    patients_linked: int = 0
    patients_total: int = 0
    professionals_linked: int = 0
    professionals_total: int = 0
    coverage_pct: float = 0.0


class IdentityStatsResponse(BaseModel):
    total_pessoas: int = 0
    patients_linked: int = 0
    patients_total: int = 0
    professionals_linked: int = 0
    professionals_total: int = 0
    coverage_pct: float = 0.0
    tenants: list[IdentityTenantStats] = Field(default_factory=list)
