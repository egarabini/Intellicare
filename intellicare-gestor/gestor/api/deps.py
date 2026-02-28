"""Dependências FastAPI do intellicare-gestor.

Fornece:
  - get_db: session de banco para o tenant atual
  - get_tenant_ctx: TenantContext (suporte a single e multi-tenant)
  - get_audit: AuditService já com session
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from intellicare_core.tenant import TenantAwareSessionFactory, TenantContext

from gestor.config import config
from gestor.services.audit_service import AuditService


def get_session_factory(request: Request) -> TenantAwareSessionFactory:
    """Retorna a factory de sessions do app.state."""
    return request.app.state.session_factory


async def get_tenant_ctx(request: Request) -> TenantContext:
    """Retorna o TenantContext da requisição.

    - Multi-tenant: extrai do request.state (injetado pelo middleware auth)
    - Single-tenant (dev): retorna TenantContext.default()
    """
    if config.multi_tenant_enabled:
        ctx = getattr(request.state, "tenant_context", None)
        if ctx is None:
            # Middleware não foi executado — fallback seguro
            return TenantContext.default()
        return ctx
    return TenantContext.default()


async def get_db(
    request: Request,
    ctx: TenantContext = Depends(get_tenant_ctx),
    factory: TenantAwareSessionFactory = Depends(get_session_factory),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency que fornece uma session para o schema do tenant.

    Faz commit automático em caso de sucesso e rollback em exceções.
    """
    session = await factory.get_session(ctx)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_audit(
    session: AsyncSession = Depends(get_db),
) -> AuditService:
    """Retorna o AuditService com a session do tenant."""
    return AuditService(session)
