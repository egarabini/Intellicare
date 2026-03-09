"""CRUD de Secretarias."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from admin.models.secretaria import Secretaria
from admin.api.deps import get_db, require_platform_admin

router = APIRouter(prefix="/admin/secretarias", tags=["Secretarias"])


class SecretariaCreate(BaseModel):
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


class SecretariaUpdate(BaseModel):
    nome: str | None = None
    alias: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None
    telefone: str | None = None
    tenant_id: str | None = None
    active: bool | None = None


class SecretariaResponse(BaseModel):
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


@router.get("", response_model=list[SecretariaResponse])
async def list_secretarias(
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Lista todas as secretarias."""
    result = await session.execute(select(Secretaria).order_by(Secretaria.nome))
    return result.scalars().all()


@router.post("", response_model=SecretariaResponse, status_code=201)
async def create_secretaria(
    data: SecretariaCreate,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Cria uma secretaria."""
    existing = await session.get(Secretaria, data.id)
    if existing:
        raise HTTPException(status_code=409, detail="Secretaria já existe")
    obj = Secretaria(
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


@router.get("/{secretaria_id}", response_model=SecretariaResponse)
async def get_secretaria(
    secretaria_id: str,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Obtém uma secretaria por ID."""
    obj = await session.get(Secretaria, secretaria_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Secretaria não encontrada")
    return obj


@router.patch("/{secretaria_id}", response_model=SecretariaResponse)
async def update_secretaria(
    secretaria_id: str,
    data: SecretariaUpdate,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Atualiza uma secretaria."""
    obj = await session.get(Secretaria, secretaria_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Secretaria não encontrada")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.delete("/{secretaria_id}", status_code=204)
async def delete_secretaria(
    secretaria_id: str,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_platform_admin),
):
    """Remove uma secretaria."""
    obj = await session.get(Secretaria, secretaria_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Secretaria não encontrada")
    await session.delete(obj)
    await session.commit()
