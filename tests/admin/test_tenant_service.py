"""Testes unitarios do TenantService."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from modules.admin.schemas import TenantCreate, TenantStatusUpdate
from modules.admin.service import TenantService
from intellicare_core.contracts.base import TenantContext

# TenantContext ficticio para actor nos testes
ADMIN_CTX = TenantContext(
    tenant_id="platform",
    schema="public",
    user_id="test-admin-id",
    roles=["PLATFORM_ADMIN"],
    email="admin@test.dev",
)


@pytest.mark.asyncio
async def test_create_tenant_slug_invalido():
    """Slug com caracteres invalidos deve falhar na validacao Pydantic."""
    with pytest.raises(ValueError, match="slug"):
        TenantCreate(slug="Slug Invalido!", name="Teste", gestor_email="g@x.com")


@pytest.mark.asyncio
async def test_create_tenant_slug_curto():
    with pytest.raises(ValueError, match="slug"):
        TenantCreate(slug="ab", name="Teste", gestor_email="g@x.com")


@pytest.mark.asyncio
async def test_create_tenant_nome_curto():
    with pytest.raises(ValueError, match="name"):
        TenantCreate(slug="valid_slug", name="ab", gestor_email="g@x.com")


@pytest.mark.asyncio
@patch("modules.admin.service.get_engine")
@patch("modules.admin.service.KeycloakAdminClient")
async def test_create_tenant_slug_duplicado(mock_kc_cls, mock_engine):
    """Slug ja existente deve levantar ValueError."""
    # Simula engine retornando slug existente
    mock_conn = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    # execute retorna row (slug existe)
    mock_conn.execute = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=("exists",))))

    mock_engine_inst = MagicMock()
    mock_engine_inst.begin = MagicMock(return_value=mock_conn)
    mock_engine.return_value = mock_engine_inst

    svc = TenantService()
    with pytest.raises(ValueError, match="ja existe"):
        await svc.create_tenant(
            TenantCreate(slug="already_there", name="Dup Tenant", gestor_email="g@x.com"),
            ADMIN_CTX,
        )


@pytest.mark.asyncio
async def test_status_update_schema_invalido():
    """Status fora dos valores permitidos deve falhar no Pydantic."""
    with pytest.raises(ValueError):
        TenantStatusUpdate(status="deleted")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_create_tenant_slug_valido():
    """Slug valido deve ser aceito sem erro."""
    t = TenantCreate(slug="clinica_abc", name="Clinica ABC", gestor_email="g@abc.com")
    assert t.slug == "clinica_abc"
    assert t.name == "Clinica ABC"


@pytest.mark.asyncio
async def test_status_update_valores_validos():
    """Status 'active' e 'suspended' devem ser aceitos."""
    assert TenantStatusUpdate(status="active").status == "active"
    assert TenantStatusUpdate(status="suspended").status == "suspended"


@pytest.mark.asyncio
async def test_tenant_create_name_strip():
    """Name com espacos deve ser trimado."""
    t = TenantCreate(slug="test_slug", name="  Clinica X  ", gestor_email="g@x.com")
    assert t.name == "Clinica X"

