import pytest
from uuid import UUID

from admin.services.provisioning import ProvisioningService

class MockSession:
    async def execute(self, *args, **kwargs):
        return True
    async def commit(self):
        return True
    async def rollback(self):
        pass

@pytest.mark.asyncio
async def test_create_tenant_schema():
    session = MockSession()
    service = ProvisioningService(session)
    result = await service.create_tenant_schema(UUID("00000000-0000-0000-0000-000000000000"))
    assert result is True

@pytest.mark.asyncio
async def test_drop_tenant_schema():
    session = MockSession()
    service = ProvisioningService(session)
    result = await service.drop_tenant_schema(UUID("00000000-0000-0000-0000-000000000000"))
    assert result is True
