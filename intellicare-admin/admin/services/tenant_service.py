from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from admin.models.tenant import Estabelecimento
from admin.schemas.tenant import EstabelecimentoCreate, EstabelecimentoUpdate

class TenantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tenant(self, data: EstabelecimentoCreate, admin_id: UUID) -> Estabelecimento:
        estabelecimento = Estabelecimento(
            nome=data.nome,
            cnes=data.cnes,
            cnpj=data.cnpj,
            tipo=data.tipo,
            gestor_nome=data.gestor.get("nome") if data.gestor else None,
            gestor_email=data.gestor.get("email") if data.gestor else None,
            gestor_telefone=data.gestor.get("telefone") if data.gestor else None,
            plano_id=data.plano_id,
            criado_por=admin_id
        )
        self.session.add(estabelecimento)
        await self.session.flush()
        return estabelecimento

    async def get_tenant(self, tenant_id: UUID) -> Optional[Estabelecimento]:
        result = await self.session.execute(select(Estabelecimento).where(Estabelecimento.id == tenant_id))
        return result.scalars().first()

    async def get_tenant_by_cnpj(self, cnpj: str) -> Optional[Estabelecimento]:
        result = await self.session.execute(select(Estabelecimento).where(Estabelecimento.cnpj == cnpj))
        return result.scalars().first()
        
    async def list_tenants(self, skip: int = 0, limit: int = 100) -> List[Estabelecimento]:
        result = await self.session.execute(select(Estabelecimento).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count_tenants(self) -> int:
        from sqlalchemy import func
        result = await self.session.execute(select(func.count(Estabelecimento.id)))
        return result.scalar_one()

    async def update_tenant(self, tenant_id: UUID, obj_in: EstabelecimentoUpdate) -> Optional[Estabelecimento]:
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_tenant(tenant_id)
            
        stmt = (
            update(Estabelecimento)
            .where(Estabelecimento.id == tenant_id)
            .values(**update_data)
            .returning(Estabelecimento)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_tenant(self, tenant_id: UUID) -> bool:
        stmt = delete(Estabelecimento).where(Estabelecimento.id == tenant_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
