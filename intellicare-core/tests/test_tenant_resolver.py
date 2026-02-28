"""Testes do TenantResolver multi-fonte.

Cobertura:
    - Resolução por JWT
    - Resolução por header X-Tenant-ID
    - Resolução por subdomínio
    - Resolução por path
    - Resolução por query param
    - Prioridade entre fontes
    - Subdomínios reservados
    - Validação de slug
    - Edge cases
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import Any, Optional

from intellicare_core.tenant.resolver import (
    TenantResolver,
    ResolvedTenant,
    _RESERVED_SUBDOMAINS,
)


# ── Fake Request Object ────────────────────────────────────

@dataclass
class FakeURL:
    path: str = "/"


@dataclass
class FakeState:
    user: Optional[dict] = None
    tenant_context: Any = None
    tenant_resolved: Any = None


@dataclass
class FakeRequest:
    _headers: dict = field(default_factory=dict)
    url: FakeURL = field(default_factory=FakeURL)
    _query_params: dict = field(default_factory=dict)
    state: FakeState = field(default_factory=FakeState)

    @property
    def headers(self):
        return self._headers

    @property
    def query_params(self):
        return self._query_params


# ── Fixtures ───────────────────────────────────────────────

@pytest.fixture
def resolver():
    return TenantResolver(
        platform_domains=["intellicare.ia.br"],
        module_domains=["saudeconectada.com.br"],
    )


@pytest.fixture
def resolver_all():
    """Resolver com todas as fontes habilitadas."""
    return TenantResolver(
        platform_domains=["intellicare.ia.br"],
        module_domains=["saudeconectada.com.br"],
        enable_path_resolution=True,
        enable_query_resolution=True,
    )


# ════════════════════════════════════════════════════════════
# 1. JWT Resolution
# ════════════════════════════════════════════════════════════

class TestJWTResolution:
    def test_resolve_from_jwt(self, resolver):
        request = FakeRequest()
        jwt = {"tenant_id": "hospital_einstein", "sub": "user1"}
        result = resolver.resolve(request, jwt_payload=jwt)
        assert result.is_resolved
        assert result.tenant_id == "hospital_einstein"
        assert result.source == "jwt"
        assert result.confidence == "high"

    def test_jwt_takes_priority_over_header(self, resolver):
        request = FakeRequest(_headers={
            "X-Tenant-ID": "hospital_other",
            "host": "hospital_another.saudeconectada.com.br",
        })
        jwt = {"tenant_id": "hospital_einstein"}
        result = resolver.resolve(request, jwt_payload=jwt)
        assert result.tenant_id == "hospital_einstein"
        assert result.source == "jwt"

    def test_jwt_without_tenant_id(self, resolver):
        request = FakeRequest()
        jwt = {"sub": "user1"}  # No tenant_id
        result = resolver.resolve(request, jwt_payload=jwt)
        assert not result.is_resolved

    def test_jwt_invalid_tenant_id(self, resolver):
        request = FakeRequest()
        jwt = {"tenant_id": "a"}  # Too short
        result = resolver.resolve(request, jwt_payload=jwt)
        assert not result.is_resolved


# ════════════════════════════════════════════════════════════
# 2. Header Resolution
# ════════════════════════════════════════════════════════════

class TestHeaderResolution:
    def test_resolve_from_header(self, resolver):
        request = FakeRequest(_headers={"X-Tenant-ID": "hospital_abc"})
        result = resolver.resolve(request)
        assert result.is_resolved
        assert result.tenant_id == "hospital_abc"
        assert result.source == "header"
        assert result.confidence == "medium"

    def test_header_case_insensitive(self, resolver):
        request = FakeRequest(_headers={"X-Tenant-ID": "Hospital_ABC"})
        result = resolver.resolve(request)
        assert result.tenant_id == "hospital_abc"

    def test_header_whitespace_stripped(self, resolver):
        request = FakeRequest(_headers={"X-Tenant-ID": "  hospital_abc  "})
        result = resolver.resolve(request)
        assert result.tenant_id == "hospital_abc"

    def test_header_empty(self, resolver):
        request = FakeRequest(_headers={"X-Tenant-ID": ""})
        result = resolver.resolve(request)
        assert not result.is_resolved

    def test_header_takes_priority_over_subdomain(self, resolver):
        request = FakeRequest(_headers={
            "X-Tenant-ID": "hospital_header",
            "host": "hospital_subdomain.saudeconectada.com.br",
        })
        result = resolver.resolve(request)
        assert result.tenant_id == "hospital_header"
        assert result.source == "header"


# ════════════════════════════════════════════════════════════
# 3. Subdomain Resolution
# ════════════════════════════════════════════════════════════

class TestSubdomainResolution:
    def test_resolve_from_subdomain_module_domain(self, resolver):
        request = FakeRequest(_headers={"host": "hospital_abc.saudeconectada.com.br"})
        result = resolver.resolve(request)
        assert result.is_resolved
        assert result.tenant_id == "hospital_abc"
        assert result.source == "subdomain"
        assert result.confidence == "medium"

    def test_resolve_from_subdomain_platform_domain(self, resolver):
        request = FakeRequest(_headers={"host": "hospital_abc.intellicare.ia.br"})
        result = resolver.resolve(request)
        assert result.is_resolved
        assert result.tenant_id == "hospital_abc"

    def test_subdomain_hyphen_normalized(self, resolver):
        """Hyphens in subdomain should be converted to underscores."""
        request = FakeRequest(_headers={"host": "hospital-sao-paulo.saudeconectada.com.br"})
        result = resolver.resolve(request)
        assert result.tenant_id == "hospital_sao_paulo"
        assert result.raw_value == "hospital-sao-paulo"

    def test_reserved_subdomain_admin(self, resolver):
        request = FakeRequest(_headers={"host": "admin.intellicare.ia.br"})
        result = resolver.resolve(request)
        assert not result.is_resolved

    def test_reserved_subdomain_portal(self, resolver):
        request = FakeRequest(_headers={"host": "portal.intellicare.ia.br"})
        result = resolver.resolve(request)
        assert not result.is_resolved

    def test_reserved_subdomain_modules(self, resolver):
        """All IntelliCare module names should be reserved."""
        modules = ["florence", "oswaldo", "zilda", "donabedian", "wanda",
                    "comunicacao", "geralda", "grahame", "minerva", "pierre"]
        for mod in modules:
            request = FakeRequest(_headers={"host": f"{mod}.saudeconectada.com.br"})
            result = resolver.resolve(request)
            assert not result.is_resolved, f"{mod} deveria ser reservado"

    def test_root_domain_no_subdomain(self, resolver):
        request = FakeRequest(_headers={"host": "saudeconectada.com.br"})
        result = resolver.resolve(request)
        assert not result.is_resolved

    def test_unknown_domain(self, resolver):
        request = FakeRequest(_headers={"host": "hospital.otherdomain.com"})
        result = resolver.resolve(request)
        assert not result.is_resolved

    def test_host_with_port(self, resolver):
        request = FakeRequest(_headers={"host": "hospital_abc.saudeconectada.com.br:443"})
        result = resolver.resolve(request)
        assert result.tenant_id == "hospital_abc"


# ════════════════════════════════════════════════════════════
# 4. Path Resolution
# ════════════════════════════════════════════════════════════

class TestPathResolution:
    def test_resolve_from_path(self, resolver_all):
        request = FakeRequest(url=FakeURL(path="/api/v1/hospital_einstein/oswaldo/patients"))
        result = resolver_all.resolve(request)
        assert result.is_resolved
        assert result.tenant_id == "hospital_einstein"
        assert result.source == "path"
        assert result.confidence == "low"

    def test_path_disabled_by_default(self, resolver):
        request = FakeRequest(url=FakeURL(path="/api/v1/hospital_einstein/oswaldo/patients"))
        result = resolver.resolve(request)
        assert not result.is_resolved  # Path disabled by default

    def test_path_module_name_excluded(self, resolver_all):
        """Module names in path should not be resolved as tenants."""
        request = FakeRequest(url=FakeURL(path="/api/v1/florence/patients"))
        result = resolver_all.resolve(request)
        assert not result.is_resolved


# ════════════════════════════════════════════════════════════
# 5. Query Resolution
# ════════════════════════════════════════════════════════════

class TestQueryResolution:
    def test_resolve_from_query(self, resolver_all):
        request = FakeRequest(_query_params={"tenant": "hospital_abc"})
        result = resolver_all.resolve(request)
        assert result.is_resolved
        assert result.tenant_id == "hospital_abc"
        assert result.source == "query"

    def test_query_disabled_by_default(self, resolver):
        request = FakeRequest(_query_params={"tenant": "hospital_abc"})
        result = resolver.resolve(request)
        assert not result.is_resolved


# ════════════════════════════════════════════════════════════
# 6. Edge Cases
# ════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_no_sources_returns_unresolved(self, resolver):
        request = FakeRequest()
        result = resolver.resolve(request)
        assert not result.is_resolved
        assert result.source == "none"

    def test_invalid_slug_too_short(self, resolver):
        request = FakeRequest(_headers={"X-Tenant-ID": "ab"})
        result = resolver.resolve(request)
        assert not result.is_resolved

    def test_invalid_slug_special_chars(self, resolver):
        request = FakeRequest(_headers={"X-Tenant-ID": "hospital@abc"})
        result = resolver.resolve(request)
        assert not result.is_resolved

    def test_invalid_slug_starts_with_underscore(self, resolver):
        request = FakeRequest(_headers={"X-Tenant-ID": "_hospital"})
        result = resolver.resolve(request)
        assert not result.is_resolved

    def test_resolved_tenant_repr(self):
        r = ResolvedTenant(tenant_id="abc", source="jwt", confidence="high")
        assert "abc" in repr(r)
        assert "jwt" in repr(r)

    def test_unresolved_tenant_repr(self):
        r = ResolvedTenant(tenant_id=None, source="none", confidence="none")
        assert "unresolved" in repr(r)


# ════════════════════════════════════════════════════════════
# 7. Priority Chain
# ════════════════════════════════════════════════════════════

class TestPriorityChain:
    def test_full_priority_jwt_wins(self, resolver_all):
        """JWT > Header > Subdomain > Path > Query"""
        request = FakeRequest(
            _headers={
                "X-Tenant-ID": "from_header",
                "host": "from_subdomain.saudeconectada.com.br",
            },
            url=FakeURL(path="/api/v1/from_path/resource"),
            _query_params={"tenant": "from_query"},
        )
        jwt = {"tenant_id": "from_jwt"}
        result = resolver_all.resolve(request, jwt_payload=jwt)
        assert result.tenant_id == "from_jwt"

    def test_header_wins_over_subdomain(self, resolver_all):
        request = FakeRequest(
            _headers={
                "X-Tenant-ID": "from_header",
                "host": "from_subdomain.saudeconectada.com.br",
            },
        )
        result = resolver_all.resolve(request)
        assert result.tenant_id == "from_header"

    def test_subdomain_wins_over_path(self, resolver_all):
        request = FakeRequest(
            _headers={"host": "from_subdomain.saudeconectada.com.br"},
            url=FakeURL(path="/api/v1/from_path/resource"),
        )
        result = resolver_all.resolve(request)
        assert result.tenant_id == "from_subdomain"

    def test_path_wins_over_query(self, resolver_all):
        request = FakeRequest(
            url=FakeURL(path="/api/v1/from_path/resource"),
            _query_params={"tenant": "from_query"},
        )
        result = resolver_all.resolve(request)
        assert result.tenant_id == "from_path"


# ════════════════════════════════════════════════════════════
# 8. Reserved Subdomains Coverage
# ════════════════════════════════════════════════════════════

class TestReservedSubdomains:
    def test_all_reserved_subdomains_present(self):
        """Validate expected reserved subdomains exist."""
        expected = {"admin", "portal", "api", "keycloak", "traefik", "grafana",
                    "florence", "oswaldo", "minerva", "pierre"}
        assert expected.issubset(_RESERVED_SUBDOMAINS)

    def test_custom_reserved_subdomains(self):
        """Test resolver with custom reserved list."""
        resolver = TenantResolver(
            module_domains=["example.com"],
            reserved_subdomains=frozenset({"custom", "reserved"}),
        )
        request = FakeRequest(_headers={"host": "custom.example.com"})
        result = resolver.resolve(request)
        assert not result.is_resolved

        request = FakeRequest(_headers={"host": "valid_tenant.example.com"})
        result = resolver.resolve(request)
        assert result.is_resolved
