"""Fixtures para testes do intellicare-gestor."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gestor.models.base import Base
from gestor.models import TenantUser, Role, UserRole, Sector, TenantSetting, LocalAuditLog


# SQLite em memória para testes (sem Docker)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest_asyncio.fixture
async def sample_role(session: AsyncSession) -> Role:
    role = Role(name="test_role", display_name="Test Role", permissions=["oswaldo.ver"])
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


@pytest_asyncio.fixture
async def sample_user(session: AsyncSession) -> TenantUser:
    user = TenantUser(nome="Fulano de Tal", email="fulano@test.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_role(session: AsyncSession) -> Role:
    role = Role(name="admin_local", display_name="Administrador Local", is_system=True, permissions=["*"])
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role
