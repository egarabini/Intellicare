"""Tests for TenantService — business logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, UTC

from admin.schemas.tenant_schemas import TenantCreate, TenantUpdate, ModuleUpdate


class TestTenantServiceCreate:
    """Test tenant creation logic."""

    @pytest.mark.asyncio
    async def test_create_generates_slug(self, mock_session, sample_tenant_data):
        """Tenant creation should generate slug from nome_fantasia."""
        from admin.services.tenant_service import TenantService

        # Mock: no existing tenant with same CNPJ or slug
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TenantService(session=mock_session)
        data = TenantCreate(**sample_tenant_data)

        tenant = await service.create(data, actor_id="admin:test")

        assert tenant.tenant_id == "hospital_einstein"
        assert tenant.status == "trial"
        assert tenant.trial_expires_at is not None
        assert mock_session.add.called

    @pytest.mark.asyncio
    async def test_create_rejects_invalid_cnpj(self, mock_session):
        """Tenant creation should reject invalid CNPJ."""
        from admin.services.tenant_service import TenantService

        service = TenantService(session=mock_session)
        data = TenantCreate(
            nome_fantasia="Test",
            razao_social="Test LTDA",
            cnpj="00.000.000/0000-00",
            email_admin="test@test.com",
        )

        with pytest.raises(ValueError, match="CNPJ inválido"):
            await service.create(data, actor_id="admin:test")

    @pytest.mark.asyncio
    async def test_create_rejects_duplicate_cnpj(self, mock_session, sample_tenant_data):
        """Tenant creation should reject duplicate CNPJ."""
        from admin.services.tenant_service import TenantService

        # Mock: existing tenant with same CNPJ
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # existing tenant
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TenantService(session=mock_session)
        data = TenantCreate(**sample_tenant_data)

        with pytest.raises(ValueError, match="já cadastrado"):
            await service.create(data, actor_id="admin:test")


class TestTenantServiceSuspend:
    """Test tenant suspension logic."""

    @pytest.mark.asyncio
    async def test_suspend_sets_status(self, mock_session):
        """Suspending a tenant should set status and timestamp."""
        from admin.services.tenant_service import TenantService
        from admin.models.tenant import Tenant

        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.tenant_id = "hospital_test"

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_tenant
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TenantService(session=mock_session)
        result = await service.suspend("hospital_test", reason="Billing overdue", actor_id="admin:test")

        assert result.status == "suspended"
        assert result.suspended_at is not None

    @pytest.mark.asyncio
    async def test_suspend_nonexistent_returns_none(self, mock_session):
        """Suspending a nonexistent tenant should return None."""
        from admin.services.tenant_service import TenantService

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TenantService(session=mock_session)
        result = await service.suspend("nonexistent", reason="Test", actor_id="admin:test")

        assert result is None


class TestTenantServiceActivate:
    """Test tenant activation logic."""

    @pytest.mark.asyncio
    async def test_activate_clears_suspension(self, mock_session):
        """Activating a tenant should clear suspended_at."""
        from admin.services.tenant_service import TenantService
        from admin.models.tenant import Tenant

        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.tenant_id = "hospital_test"

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_tenant
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = TenantService(session=mock_session)
        result = await service.activate("hospital_test", actor_id="admin:test")

        assert result.status == "active"
        assert result.suspended_at is None


class TestTenantServiceModules:
    """Test module management logic."""

    @pytest.mark.asyncio
    async def test_update_modules_rejects_outside_plan(self, mock_session):
        """Enabling a module not in the plan should raise ValueError."""
        from admin.services.tenant_service import TenantService
        from admin.models.tenant import Tenant
        from admin.models.plan import Plan

        mock_plan = MagicMock(spec=Plan)
        mock_plan.name = "basico"
        mock_plan.modules_included = ["zilda", "florence"]

        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.tenant_id = "hospital_test"
        mock_tenant.plan = mock_plan

        # First call returns tenant, second call returns no existing module
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = AsyncMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = mock_tenant
            else:
                result.scalar_one_or_none.return_value = None
            return result

        mock_session.execute = mock_execute

        service = TenantService(session=mock_session)
        modules = [ModuleUpdate(module_name="wanda", enabled=True)]

        with pytest.raises(ValueError, match="não disponível no plano"):
            await service.update_modules("hospital_test", modules, actor_id="admin:test")
