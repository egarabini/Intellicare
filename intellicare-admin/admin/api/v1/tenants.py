from typing import Any
from uuid import UUID
from admin.db import get_db
from admin.api.deps import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from admin.schemas.tenant import EstabelecimentoCreate, EstabelecimentoResponse, EstabelecimentoUpdate, EstabelecimentoListResponse
from admin.services.tenant_service import TenantRepository
from fastapi import BackgroundTasks
from admin.workers.provisioning_worker import process_provisioning_queue
from admin.schemas.tenant import EstabelecimentoCreate, EstabelecimentoResponse, EstabelecimentoUpdate, EstabelecimentoListResponse
from admin.services.tenant_service import TenantRepository

router = APIRouter()

@router.post(
    "/estabelecimentos",
    response_model=EstabelecimentoResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_estabelecimento(
    estabelecimento_in: EstabelecimentoCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    # TODO: current_user: dict = Depends(get_current_user)
) -> Any:
    """
    Cria um novo estabelecimento (tenant).
    Acesso restrito a PLATFORM_ADMIN.
    """
    # Exemplo de admin_id para teste (substituir depois pelo id real do token auth)
    dummy_admin_id = UUID('00000000-0000-0000-0000-000000000000') 
    
    tenant_repo = TenantRepository(db)
    
    # Validações de negócio
    if await tenant_repo.get_tenant_by_cnpj(estabelecimento_in.cnpj):
         raise HTTPException(
            status_code=400,
            detail="Estabelecimento com este CNPJ já existe."
        )

    estabelecimento = await tenant_repo.create_tenant(data=estabelecimento_in, admin_id=dummy_admin_id)
    await db.commit()
    await db.refresh(estabelecimento)
    
    # Disparar worker assíncrono para o provisionamento
    background_tasks.add_task(
        process_provisioning_queue,
        estabelecimento.id,
        estabelecimento_in.gestor,
        estabelecimento.nome
    )
    
    return estabelecimento

@router.get(
    "/estabelecimentos",
    response_model=EstabelecimentoListResponse,
)
async def get_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    Lista todos os estabelecimentos paginados.
    Acesso restrito a PLATFORM_ADMIN.
    """
    tenant_repo = TenantRepository(db)
    items = await tenant_repo.list_tenants(skip=skip, limit=limit)
    total = await tenant_repo.count_tenants()
    
    return {
        "items": items,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit
    }

@router.get(
    "/estabelecimentos/{id}",
    response_model=EstabelecimentoResponse,
)
async def get_estabelecimento(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Obtém detalhes do estabelecimento por ID.
    Acesso restrito a PLATFORM_ADMIN.
    """
    tenant_repo = TenantRepository(db)
    estabelecimento = await tenant_repo.get_tenant(id)
    if not estabelecimento:
         raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")
    return estabelecimento

@router.patch(
    "/estabelecimentos/{id}",
    response_model=EstabelecimentoResponse,
)
async def update_estabelecimento(
    id: UUID,
    estabelecimento_in: EstabelecimentoUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Atualiza detalhes do estabelecimento.
    Acesso restrito a PLATFORM_ADMIN.
    """
    tenant_repo = TenantRepository(db)
    estabelecimento = await tenant_repo.get_tenant(id)
    if not estabelecimento:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")
        
    updated_estabelecimento = await tenant_repo.update_tenant(id, estabelecimento_in)
    await db.commit()
    await db.refresh(updated_estabelecimento)
    return updated_estabelecimento

@router.delete(
    "/estabelecimentos/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_estabelecimento(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove (soft delete ou cascade dependendo da regar de negocio) um estabelecimento.
    Acesso restrito a PLATFORM_ADMIN.
    """
    tenant_repo = TenantRepository(db)
    estabelecimento = await tenant_repo.get_tenant(id)
    if not estabelecimento:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")
    
    await tenant_repo.delete_tenant(id)
    await db.commit()
    return None
