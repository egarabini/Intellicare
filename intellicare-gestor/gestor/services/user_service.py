"""UserService — CRUD de usuários do tenant com validações de negócio."""

import uuid
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.models.role import Role, UserRole
from gestor.models.user import TenantUser
from gestor.schemas.user_schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Listagem ──────────────────────────────────────────────

    async def list_users(
        self,
        active_only: bool = True,
        sector_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TenantUser]:
        q = select(TenantUser)
        if active_only:
            q = q.where(TenantUser.active == True)
        if sector_id:
            q = q.where(TenantUser.sector_id == sector_id)
        q = q.limit(limit).offset(offset)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_user(self, user_id: uuid.UUID) -> TenantUser:
        user = await self._session.get(TenantUser, user_id)
        if not user:
            raise HTTPException(404, f"Usuário {user_id} não encontrado")
        return user

    # ── Criação ───────────────────────────────────────────────

    async def create_user(
        self,
        data: UserCreate,
        max_users: Optional[int] = None,
    ) -> TenantUser:
        # Validar limite de usuários do plano
        if max_users is not None:
            count = await self._count_active_users()
            if count >= max_users:
                raise HTTPException(
                    402,
                    f"Limite de usuários atingido para seu plano ({max_users}). "
                    "Faça upgrade para adicionar mais usuários.",
                )

        # Verificar email duplicado
        existing = await self._session.execute(
            select(TenantUser).where(TenantUser.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, f"Email '{data.email}' já está em uso")

        user = TenantUser(
            nome=data.nome,
            email=data.email,
            cpf=data.cpf,
            cargo=data.cargo,
            conselho=data.conselho,
            sector_id=data.sector_id,
            invited_at=datetime.now(UTC),
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    # ── Atualização ───────────────────────────────────────────

    async def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> TenantUser:
        user = await self.get_user(user_id)

        # Não permitir desativar o último admin
        if data.active is False and user.active:
            await self._check_last_admin(user_id)

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)

        await self._session.flush()
        await self._session.refresh(user)
        return user

    # ── Desativação (soft delete) ─────────────────────────────

    async def deactivate_user(self, user_id: uuid.UUID) -> TenantUser:
        user = await self.get_user(user_id)
        if not user.active:
            raise HTTPException(400, "Usuário já está inativo")

        await self._check_last_admin(user_id)

        user.active = False
        await self._session.flush()
        await self._session.refresh(user)
        return user

    # ── Helpers privados ──────────────────────────────────────

    async def _count_active_users(self) -> int:
        result = await self._session.execute(
            select(func.count()).where(TenantUser.active == True)
        )
        return result.scalar_one()

    async def _check_last_admin(self, user_id: uuid.UUID) -> None:
        """Garante que não é o último admin_local."""
        # Contar usuários ativos com role admin_local
        admin_role = await self._session.execute(
            select(Role).where(Role.name == "admin_local")
        )
        role = admin_role.scalar_one_or_none()
        if not role:
            return

        admin_count_q = (
            select(func.count())
            .select_from(UserRole)
            .join(TenantUser, TenantUser.id == UserRole.user_id)
            .where(
                UserRole.role_id == role.id,
                TenantUser.active == True,
            )
        )
        count = (await self._session.execute(admin_count_q)).scalar_one()

        # Verificar se o usuário a ser desativado é admin
        is_admin_q = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id,
        )
        is_admin = (await self._session.execute(is_admin_q)).scalar_one_or_none()

        if is_admin and count <= 1:
            raise HTTPException(
                400,
                "Não é possível desativar o único administrador local. "
                "Atribua a role admin_local a outro usuário antes.",
            )
