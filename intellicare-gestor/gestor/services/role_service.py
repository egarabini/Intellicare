"""RoleService — RBAC: roles e permissões do tenant."""

import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.models.role import Role, UserRole
from gestor.permissions import validate_permissions
from gestor.schemas.role_schemas import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_roles(self) -> list[Role]:
        result = await self._session.execute(select(Role))
        return list(result.scalars().all())

    async def get_role(self, role_id: uuid.UUID) -> Role:
        role = await self._session.get(Role, role_id)
        if not role:
            raise HTTPException(404, f"Role {role_id} não encontrada")
        return role

    async def create_role(self, data: RoleCreate) -> Role:
        # Nome único
        existing = await self._session.execute(
            select(Role).where(Role.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, f"Role '{data.name}' já existe")

        role = Role(
            name=data.name,
            display_name=data.display_name or data.name.replace("_", " ").title(),
            is_system=False,
            permissions=data.permissions,
        )
        self._session.add(role)
        await self._session.flush()
        await self._session.refresh(role)
        return role

    async def update_role(self, role_id: uuid.UUID, data: RoleUpdate) -> Role:
        role = await self.get_role(role_id)

        if data.display_name is not None:
            role.display_name = data.display_name

        if data.permissions is not None:
            invalid = validate_permissions(data.permissions)
            if invalid:
                raise HTTPException(400, f"Permissões inválidas: {invalid}")
            role.permissions = data.permissions

        await self._session.flush()
        await self._session.refresh(role)
        return role

    async def delete_role(self, role_id: uuid.UUID) -> None:
        role = await self.get_role(role_id)
        if role.is_system:
            raise HTTPException(400, "Roles do sistema não podem ser excluídas")
        await self._session.delete(role)
        await self._session.flush()

    async def assign_role_to_user(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        assigned_by: Optional[uuid.UUID] = None,
    ) -> UserRole:
        await self.get_role(role_id)  # valida existência

        # Evitar duplicata
        existing = await self._session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, "Usuário já possui essa role")

        ur = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self._session.add(ur)
        await self._session.flush()
        return ur

    async def remove_role_from_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        existing = await self._session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        ur = existing.scalar_one_or_none()
        if not ur:
            raise HTTPException(404, "Usuário não possui essa role")
        await self._session.delete(ur)
        await self._session.flush()

    async def get_user_permissions(self, user_id: uuid.UUID) -> list[str]:
        """Retorna todas as permissões consolidadas do usuário."""
        result = await self._session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        roles = result.scalars().all()
        permissions: set[str] = set()
        for role in roles:
            permissions.update(role.permissions or [])
        return list(permissions)
