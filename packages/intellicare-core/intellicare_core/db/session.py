"""
TenantAwareSessionFactory - sessao SQLAlchemy scoped por schema PostgreSQL.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext

_engine = None


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _make_engine(database_url: str):
    return create_async_engine(
        database_url,
        poolclass=NullPool,
        pool_pre_ping=True,
        echo=get_settings().environment == "development",
    )


def get_engine():
    global _engine
    if _engine is None:
        _engine = _make_engine(get_settings().database_url)
    return _engine


class TenantAwareSessionFactory:
    """Factory reutilizavel para sessoes scoped por tenant."""

    def __init__(self) -> None:
        self._factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self, ctx: TenantContext) -> AsyncGenerator[AsyncSession, None]:
        async with self._factory() as session:
            schema = _quote_identifier(ctx.schema)
            await session.execute(text(f"SET search_path TO {schema}, public"))
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


@asynccontextmanager
async def tenant_session(ctx: TenantContext) -> AsyncGenerator[AsyncSession, None]:
    factory = TenantAwareSessionFactory()
    async with factory.session(ctx) as session:
        yield session


async def check_db_connection() -> bool:
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
