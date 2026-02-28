"""SQLAlchemy async engine factory for Wanda (EF-W001)."""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine(
    database_url: str = "postgresql+asyncpg://wanda:wanda@localhost:5432/intellicare",
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> AsyncEngine:
    """Create or return the async SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection URL (asyncpg driver).
        echo: Log SQL statements.
        pool_size: Connection pool size.
        max_overflow: Extra connections allowed beyond pool_size.

    Returns:
        AsyncEngine instance (singleton).
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
        )
        logger.info("SQLAlchemy async engine created: %s", database_url.split("@")[-1])
    return _engine


def get_session_factory(
    engine: Optional[AsyncEngine] = None,
) -> async_sessionmaker[AsyncSession]:
    """Create or return the async session factory.

    Args:
        engine: Optional engine override. If None, uses the global engine.

    Returns:
        async_sessionmaker bound to the engine.
    """
    global _session_factory
    if _session_factory is None:
        if engine is None:
            engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Session factory created")
    return _session_factory


async def close_engine() -> None:
    """Dispose the engine and release all connections."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Engine disposed")
