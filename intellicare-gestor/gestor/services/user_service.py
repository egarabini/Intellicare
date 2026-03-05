import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from gestor.models.user import TenantUser
from gestor.schemas.user_schemas import TenantUserCreate, TenantUserUpdate

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: uuid.UUID) -> Optional[TenantUser]:
        result = await self.session.execute(select(TenantUser).where(TenantUser.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[TenantUser]:
        result = await self.session.execute(select(TenantUser).where(TenantUser.email == email))
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[TenantUser]:
        result = await self.session.execute(select(TenantUser).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create_user(self, user_data: TenantUserCreate, keycloak_id: Optional[str] = None) -> TenantUser:
        user = TenantUser(
            **user_data.model_dump(),
            keycloak_user_id=keycloak_id,
            invited_at=datetime.now(timezone.utc)
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_user(self, user_id: uuid.UUID, user_data: TenantUserUpdate) -> Optional[TenantUser]:
        user = await self.get_user(user_id)
        if not user:
            return None
            
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
            
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False
        user.active = False
        await self.session.flush()
        # TODO: Sincronizar inativação com Keycloak
        return True
