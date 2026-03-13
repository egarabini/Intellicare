from __future__ import annotations

import pytest

from intellicare_core.contracts import TenantContext


@pytest.fixture
def tenant_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug="test_tenant",
        user_id="user-123",
        roles=["CLINICO"],
        email="test@test.local",
    )
