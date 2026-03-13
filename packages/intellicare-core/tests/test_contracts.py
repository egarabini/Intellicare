from __future__ import annotations

import pytest

from intellicare_core.contracts import BaseModule, TenantContext


def test_tenant_context_schema() -> None:
    ctx = TenantContext.from_slug("acme", "u1", ["CLINICO"])
    assert ctx.schema == "tenant_acme"
    assert ctx.tenant_id == "acme"


def test_tenant_context_has_role() -> None:
    ctx = TenantContext.from_slug("acme", "u1", ["PLATFORM_ADMIN", "TENANT_GESTOR"])
    assert ctx.has_role("PLATFORM_ADMIN")
    assert not ctx.has_role("CLINICO")


def test_tenant_context_immutable() -> None:
    ctx = TenantContext.from_slug("acme", "u1", [])
    with pytest.raises((AttributeError, TypeError)):
        ctx.tenant_id = "other"  # type: ignore[misc]


def test_base_module_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseModule()  # type: ignore[abstract]
