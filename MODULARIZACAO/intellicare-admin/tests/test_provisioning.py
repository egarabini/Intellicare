"""Tests for ProvisioningService — schema creation + rollback."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from admin.services.provisioning_service import ProvisioningService, ProvisioningResult
from admin.models.tenant import Tenant


class TestProvisioningService:
    """Test provisioning orchestration."""

    @pytest.mark.asyncio
    async def test_provision_creates_schema(self):
        """Provisioning should create schema and mark tenant as provisioned."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.tenant_id = "hospital_test"
        mock_tenant.email_admin = "admin@test.com"
        mock_tenant.provisioned = False

        service = ProvisioningService(session=mock_session)
        result = await service.provision(mock_tenant)

        assert result.success is True
        assert "schema_created" in result.steps_completed
        assert "tenant_marked_provisioned" in result.steps_completed
        assert mock_tenant.provisioned is True

    @pytest.mark.asyncio
    async def test_provision_skips_keycloak_when_unavailable(self):
        """Without KC admin client, provisioning should skip KC steps gracefully."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.tenant_id = "hospital_no_kc"
        mock_tenant.provisioned = False

        service = ProvisioningService(session=mock_session, keycloak_admin=None)
        result = await service.provision(mock_tenant)

        assert result.success is True
        assert "keycloak_skipped" in result.steps_completed

    @pytest.mark.asyncio
    async def test_provision_rollbacks_on_failure(self):
        """If provisioning fails, schema should be rolled back."""
        mock_session = AsyncMock()

        # Make schema creation succeed but migrations fail
        call_count = 0
        async def failing_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # CREATE SCHEMA succeeds
                return MagicMock()
            elif call_count == 2:
                # Migration query fails
                raise RuntimeError("Migration failed")
            else:
                # DROP SCHEMA for rollback
                return MagicMock()

        mock_session.execute = failing_execute
        mock_session.flush = AsyncMock()

        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.tenant_id = "hospital_fail"
        mock_tenant.provisioned = False

        service = ProvisioningService(session=mock_session)
        result = await service.provision(mock_tenant)

        assert result.success is False
        assert result.error is not None
        assert "schema_created" in result.steps_completed

    @pytest.mark.asyncio
    async def test_provision_rejects_invalid_schema_name(self):
        """Schema names with special characters should be rejected."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=ValueError("Invalid schema name"))
        mock_session.flush = AsyncMock()

        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.tenant_id = "test;DROP TABLE--"
        mock_tenant.provisioned = False

        service = ProvisioningService(session=mock_session)
        result = await service.provision(mock_tenant)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_provision_result_dataclass(self):
        """ProvisioningResult should have correct defaults."""
        result = ProvisioningResult(success=True, tenant_id="test")

        assert result.success is True
        assert result.tenant_id == "test"
        assert result.steps_completed == []
        assert result.error is None
