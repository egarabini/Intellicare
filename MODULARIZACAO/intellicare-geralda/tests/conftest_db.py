"""Fixtures de banco de dados para testes do Geralda (PostgreSQL/SQLite)."""

import importlib.util
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session

from geralda.database.base import Base


def _resolve_async_test_database_url() -> str:
    """Retorna URL asyncpg para fallback de testes quando aiosqlite não está disponível."""
    raw_url = (
        os.getenv("TEST_DATABASE_URL")
        or os.getenv("INTELLICARE_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or "postgresql+asyncpg://intellicare_admin:intellicare_dev@localhost:5432/intellicare_db"
    )
    if raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "@postgres:" in raw_url:
        raw_url = raw_url.replace("@postgres:", "@localhost:")
    return raw_url


@pytest.fixture(scope="function")
def sqlite_db():
    """
    Fixture de banco SQLite em memória para testes.

    Uso:
        def test_something(sqlite_db):
            with sqlite_db.begin() as conn:
                # Síncrono
                ...

    Returns:
        Session: Sessão síncrona SQLite
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        yield conn

    engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_sqlite_db():
    """
    Fixture de banco assíncrono SQLite em memória.

    Uso:
        async def test_something(async_sqlite_db):
            async with async_sqlite_db() as session:
                # Assíncrono
                ...

    Returns:
        AsyncSession: Sessão assíncrona SQLite
    """
    has_aiosqlite = importlib.util.find_spec("aiosqlite") is not None

    if has_aiosqlite:
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            yield session
        await engine.dispose()
        return

    database_url = _resolve_async_test_database_url()
    schema = f"test_geralda_{uuid.uuid4().hex[:12]}"

    bootstrap_engine = create_async_engine(database_url, echo=False)
    async with bootstrap_engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    await bootstrap_engine.dispose()

    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"server_settings": {"search_path": schema}},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with async_session() as session:
            yield session
    finally:
        await engine.dispose()
        cleanup_engine = create_async_engine(database_url, echo=False)
        async with cleanup_engine.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await cleanup_engine.dispose()


@pytest.fixture(scope="function")
def sqlite_session_factory(sqlite_db):
    """
    Factory que cria sessões síncronas SQLite.

    Uso:
        def test_service(sqlite_session_factory):
            service = CarePlanService(sqlite_session_factory())
            ...
    """
    from sqlalchemy.orm import sessionmaker

    def _session():
        return Session(bind=sqlite_db)

    return _session
