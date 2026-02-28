"""Persistence layer for tenant custom operations."""

from __future__ import annotations

from sqlalchemy import Select, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.custom_operation import CustomOperation


class CustomOperationRepository:
    """CRUD helpers for custom operations scoped by tenant."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, operation: CustomOperation) -> CustomOperation:
        self.session.add(operation)
        await self.session.commit()
        await self.session.refresh(operation)
        return operation

    async def get(self, tenant_id: str, operation_id: str) -> CustomOperation | None:
        result = await self.session.execute(
            select(CustomOperation).where(
                CustomOperation.id == operation_id,
                CustomOperation.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id: str) -> list[CustomOperation]:
        result = await self.session.execute(
            select(CustomOperation)
            .where(CustomOperation.tenant_id == tenant_id)
            .order_by(CustomOperation.name.asc())
        )
        return list(result.scalars().all())

    async def get_by_tenant_and_name(
        self,
        tenant_id: str,
        name: str,
        resource_type: str | None = None,
    ) -> CustomOperation | None:
        query: Select[tuple[CustomOperation]] = select(CustomOperation).where(
            CustomOperation.tenant_id == tenant_id,
            CustomOperation.name == name,
        )
        if resource_type:
            query = query.where(
                or_(
                    CustomOperation.resource_type == resource_type,
                    CustomOperation.resource_type.is_(None),
                )
            ).order_by(CustomOperation.resource_type.desc())
        result = await self.session.execute(query)
        return result.scalars().first()

    async def update(self, operation: CustomOperation) -> CustomOperation:
        await self.session.commit()
        await self.session.refresh(operation)
        return operation

    async def delete(self, tenant_id: str, operation_id: str) -> bool:
        result = await self.session.execute(
            delete(CustomOperation).where(
                CustomOperation.id == operation_id,
                CustomOperation.tenant_id == tenant_id,
            )
        )
        await self.session.commit()
        return (result.rowcount or 0) > 0
