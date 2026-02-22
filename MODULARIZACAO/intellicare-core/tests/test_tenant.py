"""Testes unitarios para o pacote intellicare_core.tenant.

Cobre TenantContext, TenantAwareSessionFactory e TenantRedisClient.
"""

from __future__ import annotations

import pytest

from intellicare_core.tenant.context import TenantContext


# ═══════════════════════════════════════════════════════════════
# TenantContext
# ═══════════════════════════════════════════════════════════════

class TestTenantContext:
    """Testes para TenantContext dataclass."""

    def test_from_jwt_single_tenant(self):
        """CT-01: Token com tenant_id valido."""
        payload = {
            "sub": "user-123",
            "tenant_id": "hospital_einstein",
            "tenants": ["hospital_einstein"],
            "realm_access": {"roles": ["medico"]},
        }
        ctx = TenantContext.from_jwt(payload)

        assert ctx.tenant_id == "hospital_einstein"
        assert ctx.tenant_schema == "tenant_hospital_einstein"
        assert ctx.user_id == "user-123"
        assert "medico" in ctx.user_roles
        assert ctx.available_tenants == ["hospital_einstein"]
        assert ctx.is_multi_org is False
        assert ctx.has_tenant_selected is True

    def test_from_jwt_multi_org_no_selection(self):
        """CT-09: Usuario multi-org sem selecao (tenant_id=None)."""
        payload = {
            "sub": "dr-luiz-uuid",
            "tenant_id": None,
            "tenants": ["hospital_a", "hospital_b", "ubs_centro"],
            "realm_access": {"roles": ["medico"]},
        }
        ctx = TenantContext.from_jwt(payload)

        # Sem tenant_id e com >1 tenant, nao auto-seleciona
        assert ctx.tenant_id == "default"
        assert ctx.is_multi_org is True
        assert ctx.has_tenant_selected is False
        assert len(ctx.available_tenants) == 3

    def test_from_jwt_auto_select_single(self):
        """CT-08: Auto-select quando ha apenas 1 tenant."""
        payload = {
            "sub": "user-456",
            "tenant_id": None,
            "tenants": ["hospital_unico"],
            "realm_access": {"roles": ["enfermeiro"]},
        }
        ctx = TenantContext.from_jwt(payload)

        # Auto-select: usa o unico tenant disponivel
        assert ctx.tenant_id == "hospital_unico"
        assert ctx.tenant_schema == "tenant_hospital_unico"
        assert ctx.is_multi_org is False

    def test_from_jwt_post_selection(self):
        """CT-10: Apos selecao via token exchange."""
        payload = {
            "sub": "dr-luiz-uuid",
            "tenant_id": "hospital_b",
            "tenants": ["hospital_a", "hospital_b", "ubs_centro"],
            "realm_access": {"roles": ["medico"]},
        }
        ctx = TenantContext.from_jwt(payload)

        assert ctx.tenant_id == "hospital_b"
        assert ctx.tenant_schema == "tenant_hospital_b"
        assert ctx.is_multi_org is True
        assert ctx.has_tenant_selected is True

    def test_default_context(self):
        """CT-06: Modo single-tenant."""
        ctx = TenantContext.default()

        assert ctx.tenant_id == "default"
        assert ctx.tenant_schema == "public"
        assert ctx.user_id == "system"
        assert not ctx.is_multi_org

    def test_immutability(self):
        """TenantContext e frozen (imutavel)."""
        ctx = TenantContext.default()
        with pytest.raises(AttributeError):
            ctx.tenant_id = "outro"

    def test_invalid_tenant_id(self):
        """Rejeita tenant_id com caracteres invalidos."""
        with pytest.raises(ValueError, match="tenant_id invalido"):
            TenantContext(
                tenant_id="Hospital Einstein!",  # invalido: espacos, maiuscula, exclamacao
                tenant_schema="tenant_invalid",
                user_id="test",
            )

    def test_valid_tenant_id_patterns(self):
        """Aceita tenant_ids validos."""
        valid_ids = [
            "hospital_einstein",
            "ubs_centro_sp",
            "hospital123",
            "h01_test_tenant",
        ]
        for tid in valid_ids:
            ctx = TenantContext(
                tenant_id=tid,
                tenant_schema=f"tenant_{tid}",
                user_id="test",
            )
            assert ctx.tenant_id == tid

    def test_extract_roles_realm_and_resource(self):
        """Extrai roles de realm_access e resource_access."""
        payload = {
            "sub": "u1",
            "tenant_id": "test_org",
            "tenants": ["test_org"],
            "realm_access": {"roles": ["medico", "admin"]},
            "resource_access": {
                "intellicare-portal": {"roles": ["portal_user"]},
                "intellicare-api": {"roles": ["api_access"]},
            },
        }
        ctx = TenantContext.from_jwt(payload)
        assert "medico" in ctx.user_roles
        assert "admin" in ctx.user_roles
        assert "portal_user" in ctx.user_roles
        assert "api_access" in ctx.user_roles

    def test_repr(self):
        """Repr legivel para debug."""
        ctx = TenantContext.default()
        r = repr(ctx)
        assert "default" in r
        assert "public" in r


# ═══════════════════════════════════════════════════════════════
# TenantAwareSessionFactory - Schema Validation
# ═══════════════════════════════════════════════════════════════

class TestTenantAwareSessionFactory:
    """Testes para validacao de schema (sem banco real)."""

    def test_validate_valid_schemas(self):
        """Aceita schemas com prefixo tenant_, public ou platform."""
        from intellicare_core.tenant.session import TenantAwareSessionFactory
        # Estes nao devem levantar excecao
        TenantAwareSessionFactory._validate_schema("tenant_hospital_einstein")
        TenantAwareSessionFactory._validate_schema("tenant_ubs_centro")
        TenantAwareSessionFactory._validate_schema("public")
        TenantAwareSessionFactory._validate_schema("platform")

    def test_reject_invalid_schemas(self):
        """Rejeita schemas com nomes suspeitos (prevencao de injection)."""
        from intellicare_core.tenant.session import TenantAwareSessionFactory
        with pytest.raises(ValueError, match="Schema name invalido"):
            TenantAwareSessionFactory._validate_schema("'; DROP TABLE users; --")
        with pytest.raises(ValueError, match="Schema name invalido"):
            TenantAwareSessionFactory._validate_schema("TENANT_UPPER")
        with pytest.raises(ValueError, match="Schema name invalido"):
            TenantAwareSessionFactory._validate_schema("random_schema")


# ═══════════════════════════════════════════════════════════════
# TenantRedisClient - Key Generation
# ═══════════════════════════════════════════════════════════════

class TestTenantRedisClient:
    """Testes para geracao de keys Redis (sem Redis real)."""

    def test_key_format_without_prefix(self):
        """Keys seguem formato tenant:{id}:{key}."""
        from intellicare_core.tenant.redis import TenantRedisClient
        client = TenantRedisClient.__new__(TenantRedisClient)
        client._key_prefix = ""

        ctx = TenantContext(
            tenant_id="hospital_einstein",
            tenant_schema="tenant_hospital_einstein",
            user_id="test",
        )
        key = client._key(ctx, "zilda:cnes:2077485")
        assert key == "tenant:hospital_einstein:zilda:cnes:2077485"

    def test_key_format_with_module_prefix(self):
        """Keys com prefixo de modulo: tenant:{id}:{module}:{key}."""
        from intellicare_core.tenant.redis import TenantRedisClient
        client = TenantRedisClient.__new__(TenantRedisClient)
        client._key_prefix = "zilda"

        ctx = TenantContext(
            tenant_id="ubs_centro",
            tenant_schema="tenant_ubs_centro",
            user_id="test",
        )
        key = client._key(ctx, "cnes:2077485")
        assert key == "tenant:ubs_centro:zilda:cnes:2077485"
