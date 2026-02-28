"""Resolvedor multi-fonte de tenant.

Resolve o tenant_id da requisição a partir de múltiplas fontes,
em ordem de prioridade:

    1. JWT claim (tenant_id) — máxima prioridade, autenticado
    2. Header X-Tenant-ID — injetado pelo Traefik ou API gateway
    3. Subdomínio do Host header — {tenant}.saudeconectada.com.br
    4. URL path — /api/v1/{tenant_id}/...
    5. Query parameter — ?tenant=xxx (apenas para debug/dev)

Uso:
    from intellicare_core.tenant.resolver import TenantResolver

    resolver = TenantResolver(
        platform_domains=["intellicare.ia.br"],
        module_domains=["saudeconectada.com.br"],
    )

    tenant_id = resolver.resolve(request)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Protocol

import structlog

logger = structlog.get_logger(__name__)


# Subdomínios reservados (não são tenant slugs)
_RESERVED_SUBDOMAINS = frozenset({
    "www", "admin", "portal", "api", "keycloak", "traefik",
    "grafana", "prometheus", "docs", "status", "mail", "smtp",
    # Módulos do IntelliCare
    "florence", "oswaldo", "zilda", "donabedian", "wanda",
    "comunicacao", "geralda", "grahame", "minerva", "pierre",
})

# Regex para validar tenant slug
_TENANT_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")


class RequestLike(Protocol):
    """Protocolo mínimo para objetos request (FastAPI, Starlette, etc.)."""

    @property
    def headers(self) -> dict: ...

    @property
    def url(self) -> object: ...

    @property
    def query_params(self) -> dict: ...

    @property
    def state(self) -> object: ...


@dataclass
class ResolvedTenant:
    """Resultado da resolução de tenant.

    Attributes:
        tenant_id: Slug do tenant resolvido (ou None se não encontrado)
        source: Fonte de onde veio (jwt, header, subdomain, path, query)
        confidence: Nível de confiança (high=jwt, medium=header/subdomain, low=path/query)
        raw_value: Valor original antes de normalização
    """
    tenant_id: Optional[str]
    source: str
    confidence: str  # "high", "medium", "low"
    raw_value: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        return self.tenant_id is not None

    def __repr__(self) -> str:
        if self.is_resolved:
            return f"ResolvedTenant('{self.tenant_id}' via {self.source} [{self.confidence}])"
        return "ResolvedTenant(unresolved)"


@dataclass
class TenantResolver:
    """Resolvedor multi-fonte de tenant.

    Tenta resolver o tenant_id através de múltiplas fontes em ordem
    de prioridade. A primeira match válida é usada.

    Args:
        platform_domains: Domínios da plataforma (admin/portal/api).
            Ex: ["intellicare.ia.br"]
        module_domains: Domínios dos módulos standalone e white-label.
            Ex: ["saudeconectada.com.br"]
        header_name: Nome do header com tenant_id (default: X-Tenant-ID)
        enable_path_resolution: Permite resolver por URL path
        enable_query_resolution: Permite resolver por query param (dev only)
        reserved_subdomains: Subdomínios que não são tenant slugs
    """
    platform_domains: list[str] = field(default_factory=lambda: ["intellicare.ia.br"])
    module_domains: list[str] = field(default_factory=lambda: ["saudeconectada.com.br"])
    header_name: str = "X-Tenant-ID"
    enable_path_resolution: bool = False
    enable_query_resolution: bool = False
    reserved_subdomains: frozenset[str] = field(default_factory=lambda: _RESERVED_SUBDOMAINS)

    def resolve(
        self,
        request: RequestLike,
        jwt_payload: Optional[dict] = None,
    ) -> ResolvedTenant:
        """Resolve tenant_id a partir da requisição.

        Ordem de prioridade:
            1. JWT claim (se jwt_payload fornecido)
            2. Header X-Tenant-ID
            3. Subdomínio do Host
            4. URL path (se habilitado)
            5. Query parameter (se habilitado, dev only)

        Args:
            request: Objeto request (FastAPI/Starlette)
            jwt_payload: Claims do JWT (opcional, se já parseado)

        Returns:
            ResolvedTenant com resultado e metadados
        """
        # 1. JWT (máxima prioridade)
        if jwt_payload:
            result = self._from_jwt(jwt_payload)
            if result.is_resolved:
                logger.debug("tenant.resolved", source="jwt", tenant_id=result.tenant_id)
                return result

        # 2. Header X-Tenant-ID
        result = self._from_header(request)
        if result.is_resolved:
            logger.debug("tenant.resolved", source="header", tenant_id=result.tenant_id)
            return result

        # 3. Subdomínio (Host header)
        result = self._from_subdomain(request)
        if result.is_resolved:
            logger.debug("tenant.resolved", source="subdomain", tenant_id=result.tenant_id)
            return result

        # 4. URL path
        if self.enable_path_resolution:
            result = self._from_path(request)
            if result.is_resolved:
                logger.debug("tenant.resolved", source="path", tenant_id=result.tenant_id)
                return result

        # 5. Query parameter (dev/debug only)
        if self.enable_query_resolution:
            result = self._from_query(request)
            if result.is_resolved:
                logger.info("tenant.resolved.query_param", tenant_id=result.tenant_id,
                           warning="Query param resolution should not be used in production")
                return result

        logger.debug("tenant.unresolved", host=self._get_host(request))
        return ResolvedTenant(tenant_id=None, source="none", confidence="none")

    # ── Resolution Sources ──────────────────────────────────

    def _from_jwt(self, payload: dict) -> ResolvedTenant:
        """Resolve tenant_id do JWT claim."""
        tenant_id = payload.get("tenant_id")
        if tenant_id and self._is_valid_slug(tenant_id):
            return ResolvedTenant(
                tenant_id=tenant_id,
                source="jwt",
                confidence="high",
                raw_value=tenant_id,
            )
        return ResolvedTenant(tenant_id=None, source="jwt", confidence="none")

    def _from_header(self, request: RequestLike) -> ResolvedTenant:
        """Resolve tenant_id do header X-Tenant-ID."""
        raw = request.headers.get(self.header_name, "").strip().lower()
        if raw and self._is_valid_slug(raw):
            return ResolvedTenant(
                tenant_id=raw,
                source="header",
                confidence="medium",
                raw_value=raw,
            )
        return ResolvedTenant(tenant_id=None, source="header", confidence="none")

    def _from_subdomain(self, request: RequestLike) -> ResolvedTenant:
        """Resolve tenant_id do subdomínio do Host header.

        Exemplos:
            hospital-abc.saudeconectada.com.br → hospital_abc
            admin.intellicare.ia.br → None (reservado)
            saudeconectada.com.br → None (root, sem subdomínio)
        """
        host = self._get_host(request)
        if not host:
            return ResolvedTenant(tenant_id=None, source="subdomain", confidence="none")

        # Verificar contra todos os domínios configurados
        all_domains = self.platform_domains + self.module_domains
        for domain in all_domains:
            if host.endswith(f".{domain}"):
                # Extrair subdomínio
                subdomain = host[: -(len(domain) + 1)]  # Remove .domain.com

                # Ignorar subdomínios reservados
                if subdomain.lower() in self.reserved_subdomains:
                    return ResolvedTenant(
                        tenant_id=None, source="subdomain",
                        confidence="none", raw_value=subdomain
                    )

                # Normalizar: hyphens → underscores (slugs usam underscore)
                tenant_slug = subdomain.lower().replace("-", "_")

                if self._is_valid_slug(tenant_slug):
                    return ResolvedTenant(
                        tenant_id=tenant_slug,
                        source="subdomain",
                        confidence="medium",
                        raw_value=subdomain,
                    )

        return ResolvedTenant(tenant_id=None, source="subdomain", confidence="none")

    def _from_path(self, request: RequestLike) -> ResolvedTenant:
        """Resolve tenant_id da URL path.

        Pattern: /api/v1/{tenant_id}/...
        Exemplo: /api/v1/hospital_einstein/oswaldo/patients → hospital_einstein
        """
        path = str(getattr(request.url, "path", ""))
        # Match /api/v1/{tenant_id}/...
        match = re.match(r"/api/v1/([a-z0-9_-]+)/", path)
        if match:
            raw = match.group(1)
            tenant_slug = raw.replace("-", "_")
            # Excluir módulos conhecidos (florence, oswaldo, etc.)
            if tenant_slug not in self.reserved_subdomains and self._is_valid_slug(tenant_slug):
                return ResolvedTenant(
                    tenant_id=tenant_slug,
                    source="path",
                    confidence="low",
                    raw_value=raw,
                )

        return ResolvedTenant(tenant_id=None, source="path", confidence="none")

    def _from_query(self, request: RequestLike) -> ResolvedTenant:
        """Resolve tenant_id do query parameter (?tenant=xxx).

        ⚠️ Apenas para desenvolvimento/debug! Não usar em produção.
        """
        raw = request.query_params.get("tenant", "").strip().lower()
        if raw and self._is_valid_slug(raw):
            return ResolvedTenant(
                tenant_id=raw,
                source="query",
                confidence="low",
                raw_value=raw,
            )
        return ResolvedTenant(tenant_id=None, source="query", confidence="none")

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _get_host(request: RequestLike) -> str:
        """Extrai o hostname do request (sem porta)."""
        host = request.headers.get("host", "")
        # Remover porta se presente
        return host.split(":")[0].lower()

    @staticmethod
    def _is_valid_slug(slug: str) -> bool:
        """Valida se o slug é um tenant_id válido."""
        return bool(_TENANT_SLUG_PATTERN.match(slug))
