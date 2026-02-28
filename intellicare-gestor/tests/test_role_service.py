"""Testes para RoleService."""

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from gestor.models.role import Role, UserRole
from gestor.schemas.role_schemas import RoleCreate, RoleUpdate
from gestor.services.role_service import RoleService


class TestRoleService:
    async def test_list_roles_empty(self, session: AsyncSession):
        svc = RoleService(session)
        roles = await svc.list_roles()
        assert roles == []

    async def test_create_role(self, session: AsyncSession):
        svc = RoleService(session)
        data = RoleCreate(name="medico", permissions=["oswaldo.classificar", "florence.ver_resultados"])
        role = await svc.create_role(data)
        assert role.name == "medico"
        assert "oswaldo.classificar" in role.permissions
        assert role.is_system is False

    async def test_create_role_invalid_permission(self, session: AsyncSession):
        svc = RoleService(session)
        with pytest.raises(Exception):
            RoleCreate(name="bad", permissions=["modulo_invalido.acao"])

    async def test_create_role_duplicate(self, session: AsyncSession, sample_role: Role):
        svc = RoleService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.create_role(RoleCreate(name=sample_role.name, permissions=[]))
        assert exc.value.status_code == 409

    async def test_update_role_permissions(self, session: AsyncSession, sample_role: Role):
        svc = RoleService(session)
        updated = await svc.update_role(sample_role.id, RoleUpdate(permissions=["florence.analisar"]))
        assert "florence.analisar" in updated.permissions
        assert "oswaldo.ver" not in updated.permissions

    async def test_get_role_not_found(self, session: AsyncSession):
        import uuid
        svc = RoleService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.get_role(uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_delete_system_role_forbidden(self, session: AsyncSession, admin_role: Role):
        svc = RoleService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.delete_role(admin_role.id)
        assert exc.value.status_code == 400

    async def test_get_user_permissions(self, session: AsyncSession, sample_user, sample_role: Role):
        svc = RoleService(session)
        await svc.assign_role_to_user(sample_user.id, sample_role.id)
        perms = await svc.get_user_permissions(sample_user.id)
        assert "oswaldo.ver" in perms

    async def test_assign_role_duplicate(self, session: AsyncSession, sample_user, sample_role: Role):
        svc = RoleService(session)
        await svc.assign_role_to_user(sample_user.id, sample_role.id)
        with pytest.raises(HTTPException) as exc:
            await svc.assign_role_to_user(sample_user.id, sample_role.id)
        assert exc.value.status_code == 409
