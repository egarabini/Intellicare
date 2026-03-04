import pytest_asyncio
import os
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Ensure test DB SCHEMA is empty to avoid schema prefixing in Models specifically for SQLite tests
os.environ["DB_SCHEMA"] = ""

from gestor.db import Base
from gestor.api.app import app
from gestor.db import get_db

# Use a test-specific in-memory database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class MockPermissionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user_permissions = ["*"]
        request.state.user_id = "00000000-0000-0000-0000-000000000000"
        return await call_next(request)

app.add_middleware(MockPermissionMiddleware)

test_engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False, 
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=test_engine
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

from httpx import AsyncClient, ASGITransport

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
