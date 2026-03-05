"""Tenant Service aligned with Tenant Schemas."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from admin.models.tenant import Tenant
from admin.schemas.tenant_schemas import TenantCreate, TenantUpdate, TenantListResponse

class TenantService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: TenantCreate, actor_id: str) -> Tenant:
        # Check if CNPJ exists
        existing = await self.get_by_cnpj(data.cnpj)
        if existing:
            raise ValueError(f"Tenant com CNPJ {data.cnpj} já cadastrado")

        # Generate a short unique tenant_id based on cnpj digits
        short_id = "".join(filter(str.isdigit, data.cnpj))
        
        tenant = Tenant(
            tenant_id=short_id,
            nome_fantasia=data.nome_fantasia,
            razao_social=data.razao_social,
            cnpj=data.cnpj,
            email_admin=data.email_admin,
            logo_url=data.logo_url,
            cor_primaria=data.cor_primaria,
            cor_secundaria=data.cor_secundaria,
            dominio_custom=data.dominio_custom,
            plan_name=data.plan_name,
            criado_por=actor_id
        )
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def get(self, tenant_id: str) -> Optional[Tenant]:
        # Tries getting by UUID id, or string tenant_id
        stmt = select(Tenant).where((Tenant.id == tenant_id) | (Tenant.tenant_id == tenant_id))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_cnpj(self, cnpj: str) -> Optional[Tenant]:
        result = await self.session.execute(select(Tenant).where(Tenant.cnpj == cnpj))
        return result.scalars().first()
        
    async def list_tenants(self, page: int = 1, size: int = 20, status_filter: Optional[str] = None, search: Optional[str] = None) -> TenantListResponse:
        from sqlalchemy import func
        skip = (page - 1) * size
        
        stmt = select(Tenant)
        count_stmt = select(func.count(Tenant.id))
        
        if status_filter:
            stmt = stmt.where(Tenant.status == status_filter)
            count_stmt = count_stmt.where(Tenant.status == status_filter)
            
        if search:
            stmt = stmt.where(Tenant.nome_fantasia.ilike(f"%{search}%"))
            count_stmt = count_stmt.where(Tenant.nome_fantasia.ilike(f"%{search}%"))
            
        stmt = stmt.offset(skip).limit(size)
        
        items_result = await self.session.execute(stmt)
        items = list(items_result.scalars().unique().all())
        
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        from math import ceil
        pages = ceil(total / size) if size > 0 else 1

        return TenantListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    async def update(self, tenant_id: str, obj_in: TenantUpdate, actor_id: str) -> Optional[Tenant]:
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get(tenant_id)
            
        # Needs to parse UUID safely if tenant_id is passed as UUID
        from sqlalchemy import or_
        stmt = (
            update(Tenant)
            .where(or_(Tenant.id == tenant_id, Tenant.tenant_id == tenant_id))
            .values(**update_data)
            .returning(Tenant)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def suspend(self, tenant_id: str, reason: str, actor_id: str) -> Optional[Tenant]:
        stmt = (
            update(Tenant)
            .where(Tenant.tenant_id == tenant_id)
            .values(status="suspended")
            .returning(Tenant)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def activate(self, tenant_id: str, actor_id: str) -> Optional[Tenant]:
        stmt = (
            update(Tenant)
            .where(Tenant.tenant_id == tenant_id)
            .values(status="active")
            .returning(Tenant)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_modules(self, tenant_id: str, modules: list, actor_id: str):
        # Placeholder for toggling TenantModules
        pass
