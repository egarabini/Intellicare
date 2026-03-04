"""Dependências FastAPI do Grahame."""

from typing import Any
from fastapi import Request, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from grahame.api.auth import get_tenant_context
from contextlib import asynccontextmanager

async def get_db(request: Request, ctx: Any = Depends(get_tenant_context)):
    """Provê sessão AsyncSession por request isolada por tenant."""
    factory: async_sessionmaker = request.app.state.session_factory
    tenant_schema = ctx.schema_name if ctx and hasattr(ctx, "schema_name") else "public"
    
    async with factory() as session:
        try:
            if "postgresql" in str(session.bind.url):
                await session.execute(text(f"SET search_path TO {tenant_schema}"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            if "postgresql" in str(session.bind.url):
                await session.execute(text("SET search_path TO public"))

@asynccontextmanager
async def get_tenant_session_context(request: Request):
    """Context manager para endpoints que não usam injestão de dependência get_db."""
    factory: async_sessionmaker = request.app.state.session_factory
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    tenant_schema = f"tenant_{tenant_id}" if tenant_id and tenant_id != "default" else "public"

    async with factory() as session:
        try:
            if "postgresql" in str(session.bind.url):
                await session.execute(text(f"SET search_path TO {tenant_schema}"))
            yield session
        finally:
            if "postgresql" in str(session.bind.url):
                await session.execute(text("SET search_path TO public"))
