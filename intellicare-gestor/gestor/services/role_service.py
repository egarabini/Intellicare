import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from gestor.models.role import Role, UserRole
from gestor.schemas.role_schemas import RoleCreate, RoleUpdate
from gestor.permissions import validate_permission

class RoleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_role(self, role_id: uuid.UUID) -> Optional[Role]:
        result = await self.session.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def list_roles(self) -> List[Role]:
        result = await self.session.execute(select(Role))
        return list(result.scalars().all())

    async def create_role(self, role_data: RoleCreate) -> Role:
        # Validar permissões
        for perm in role_data.permissions:
            if not validate_permission(perm):
                raise ValueError(f"Permissão inválida: {perm}")
                
        role = Role(
            name=role_data.name,
            display_name=role_data.display_name,
            permissions=role_data.permissions,
            is_system=False
        )
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def update_role(self, role_id: uuid.UUID, role_data: RoleUpdate) -> Optional[Role]:
        role = await self.get_role(role_id)
        if not role:
            return None
        
        if role.is_system and role_data.permissions is not None:
            raise ValueError("Não é possível alterar permissões de roles do sistema")

        if role_data.permissions is not None:
            for perm in role_data.permissions:
                if not validate_permission(perm):
                    raise ValueError(f"Permissão inválida: {perm}")
            role.permissions = role_data.permissions
            
        if role_data.display_name is not None:
            role.display_name = role_data.display_name

        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID, assigned_by: Optional[uuid.UUID] = None) -> UserRole:
        user_role = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self.session.add(user_role)
        await self.session.flush()
        return user_role

    async def get_user_roles(self, user_id: uuid.UUID) -> List[Role]:
        query = select(Role).join(UserRole).where(UserRole.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_user_permissions_flat(self, user_id: uuid.UUID) -> List[str]:
        roles = await self.get_user_roles(user_id)
        permissions = set()
        for role in roles:
            for perm in role.permissions:
                permissions.add(perm)
        return list(permissions)
