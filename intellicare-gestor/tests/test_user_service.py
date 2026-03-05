"""Testes para UserService."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.models.role import Role, UserRole
from gestor.models.user import TenantUser
from gestor.schemas.user_schemas import TenantUserCreate as UserCreate, TenantUserUpdate as UserUpdate
from gestor.services.user_service import UserService


class TestUserService:
    async def test_create_user(self, session: AsyncSession):
        svc = UserService(session)
        data = UserCreate(nome="Dr. Silva", email="silva@hospital.com", cargo="Médico")
        user = await svc.create_user(data)
        assert user.nome == "Dr. Silva"
        assert user.email == "silva@hospital.com"
        assert user.active is True

    async def test_create_user_duplicate_email(self, session: AsyncSession, sample_user: TenantUser):
        svc = UserService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.create_user(UserCreate(nome="Outro", email=sample_user.email))
        assert exc.value.status_code == 409

    async def test_create_user_respects_max_users(self, session: AsyncSession):
        svc = UserService(session)
        await svc.create_user(UserCreate(nome="User 1", email="u1@test.com"))
        with pytest.raises(HTTPException) as exc:
            await svc.create_user(
                UserCreate(nome="User 2", email="u2@test.com"),
                max_users=1,
            )
        assert exc.value.status_code == 402

    async def test_create_user_within_limit(self, session: AsyncSession):
        svc = UserService(session)
        user = await svc.create_user(
            UserCreate(nome="User 1", email="u1@test.com"),
            max_users=10,
        )
        assert user is not None

    async def test_deactivate_user(self, session: AsyncSession, sample_user: TenantUser):
        svc = UserService(session)
        user = await svc.deactivate_user(sample_user.id)
        assert user.active is False

    async def test_deactivate_last_admin_forbidden(
        self, session: AsyncSession, sample_user: TenantUser, admin_role: Role
    ):
        # Atribuir role admin ao usuário
        session.add(UserRole(user_id=sample_user.id, role_id=admin_role.id))
        await session.commit()

        svc = UserService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.deactivate_user(sample_user.id)
        assert exc.value.status_code == 400

    async def test_update_user(self, session: AsyncSession, sample_user: TenantUser):
        svc = UserService(session)
        user = await svc.update_user(sample_user.id, UserUpdate(cargo="Enfermeiro"))
        assert user.cargo == "Enfermeiro"

    async def test_get_user_not_found(self, session: AsyncSession):
        import uuid
        svc = UserService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.get_user(uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_list_users_active_only(self, session: AsyncSession):
        svc = UserService(session)
        u1 = await svc.create_user(UserCreate(nome="Ativo", email="ativo@test.com"))
        u2 = await svc.create_user(UserCreate(nome="Inativo", email="inativo@test.com"))
        await svc.deactivate_user(u2.id)

        active = await svc.list_users(active_only=True)
        all_users = await svc.list_users(active_only=False)

        assert len(active) == 1
        assert len(all_users) == 2
