from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error
from .repository import get_pessoa_by_cpf, get_pessoa_by_id
from .schemas import PessoaFisicaIn, PessoaOut
from .services import find_or_create_by_cpf, normalize_cpf

router = APIRouter(prefix="/identity", tags=["identity"])


def _assert_platform_admin(ctx: TenantContext) -> None:
    if not ctx.has_role("PLATFORM_ADMIN"):
        raise api_error(403, "forbidden", "Role 'PLATFORM_ADMIN' necessaria")


@router.get("/pessoas/cpf/{cpf}", response_model=PessoaOut)
async def lookup_by_cpf(
    cpf: str,
    ctx: TenantContext = Depends(get_current_tenant),
):
    _assert_platform_admin(ctx)
    pessoa = await get_pessoa_by_cpf(normalize_cpf(cpf))
    if not pessoa:
        raise api_error(404, "not_found", "Pessoa nao encontrada")
    return PessoaOut(**pessoa)


@router.post("/pessoas", response_model=PessoaOut, status_code=201)
async def create_or_get_pessoa(
    payload: PessoaFisicaIn,
    ctx: TenantContext = Depends(get_current_tenant),
):
    _assert_platform_admin(ctx)
    pessoa = await find_or_create_by_cpf(payload)
    return PessoaOut(**pessoa)


@router.get("/pessoas/{pessoa_id}", response_model=PessoaOut)
async def get_pessoa(
    pessoa_id: UUID,
    ctx: TenantContext = Depends(get_current_tenant),
):
    _assert_platform_admin(ctx)
    pessoa = await get_pessoa_by_id(pessoa_id)
    if not pessoa:
        raise api_error(404, "not_found", "Pessoa nao encontrada")
    return PessoaOut(**pessoa)
