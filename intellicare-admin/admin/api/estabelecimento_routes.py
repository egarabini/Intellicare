"""CRUD de Estabelecimentos."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from admin.models.estabelecimento import Estabelecimento
from admin.api.deps import get_db, require_platform_admin

router = APIRouter(prefix="/admin/estabelecimentos", tags=["Estabelecimentos"])


class EstabelecimentoCreate(BaseModel):
    id: str
    cnes: str
    nome: str
    alias: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None
    telefone: str | None = None
    tenant_id: str | None = None


class EstabelecimentoUpdate(BaseModel):
    nome: str | None = None
    alias: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None
    telefone: str | None = None
    tenant_id: str | None = None
    active: bool | None = None


class EstabelecimentoResponse(BaseModel):
    id: str
    cnes: str
    nome: str
    alias: str | None
    endereco: str | None
    cidade: str | None
    estado: str | None
    cep: str | None
    telefone: str | None
    tenant_id: str | None
    active: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[EstabelecimentoResponse])
async def list_estabelecimentos(
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Lista todos os estabelecimentos."""
    result = await session.execute(select(Estabelecimento).order_by(Estabelecimento.nome))
    return result.scalars().all()


@router.post("", response_model=EstabelecimentoResponse, status_code=201)
async def create_estabelecimento(
    data: EstabelecimentoCreate,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Cria um estabelecimento."""
    existing = await session.get(Estabelecimento, data.id)
    if existing:
        raise HTTPException(status_code=409, detail="Estabelecimento já existe")
    obj = Estabelecimento(
        id=data.id,
        cnes=data.cnes,
        nome=data.nome,
        alias=data.alias,
        endereco=data.endereco,
        cidade=data.cidade,
        estado=data.estado,
        cep=data.cep,
        telefone=data.telefone,
        tenant_id=data.tenant_id,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.get("/{estabelecimento_id}", response_model=EstabelecimentoResponse)
async def get_estabelecimento(
    estabelecimento_id: str,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Obtém um estabelecimento por ID."""
    obj = await session.get(Estabelecimento, estabelecimento_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    return obj


@router.patch("/{estabelecimento_id}", response_model=EstabelecimentoResponse)
async def update_estabelecimento(
    estabelecimento_id: str,
    data: EstabelecimentoUpdate,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Atualiza um estabelecimento."""
    obj = await session.get(Estabelecimento, estabelecimento_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.delete("/{estabelecimento_id}", status_code=204)
async def delete_estabelecimento(
    estabelecimento_id: str,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Remove um estabelecimento."""
    obj = await session.get(Estabelecimento, estabelecimento_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    await session.delete(obj)
    await session.commit()
