from __future__ import annotations

import pytest

from intellicare_core.contracts import TenantContext


def pytest_collection_modifyitems(config, items):
    """Skip testes que requerem weasyprint se não disponível no sistema."""
    try:
        import weasyprint  # noqa: F401
    except (ImportError, OSError):
        skip_marker = pytest.mark.skip(
            reason="weasyprint não disponível (faltam libpango/libcairo no sistema)"
        )
        for item in items:
            if "pdf" in item.nodeid.lower() or "relatorio" in item.nodeid.lower():
                item.add_marker(skip_marker)


@pytest.fixture
def tenant_ctx() -> TenantContext:
    return TenantContext.from_slug(
        slug="test_tenant",
        user_id="user-123",
        roles=["CLINICO"],
        email="test@test.local",
    )
