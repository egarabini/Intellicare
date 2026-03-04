import os
import re

base_dir = r"c:\Users\egara\INTELLICARE\intellicare-donabedian\src\donabedian"

def create_auth_fallback():
    auth_code = '''"""Módulo de integração de autenticação e multitenancy para Donabedian."""

import logging
from typing import Any

from fastapi import Depends, Header

try:
    from intellicare_auth.tenant.context import TenantContext, get_tenant_context
    from intellicare_auth.fastapi.middleware import check_module_active
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False

logger = logging.getLogger(__name__)


if not _HAS_AUTH:
    class MockTenantContext:
        """Contexto de tenant local para fallback."""

        def __init__(self, tenant_id: str, tenant_name: str = "Local Tenant"):
            self.tenant_id = tenant_id
            self.tenant_name = tenant_name
            self.schema_name = f"tenant_{tenant_id}" if tenant_id else "public"
            self.settings: dict[str, Any] = {}

    async def get_tenant_context(
        x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
    ) -> Any:
        """Fallback local."""
        if not x_tenant_id:
            return MockTenantContext("default")
        return MockTenantContext(x_tenant_id)
        
    def check_module_active(module_name: str) -> Any:
        async def mock_check_active(ctx: Any = Depends(get_tenant_context)) -> Any:
            return ctx
        return mock_check_active
'''
    with open(os.path.join(base_dir, "api", "auth.py"), "w", encoding="utf-8") as f:
        f.write(auth_code)


def refactor_config():
    filepath = os.path.join(base_dir, "config.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Disable strict db_schema to allow search_path to override
    content = content.replace(
        'database_schema: str | None = "intellicare_donabedian"',
        'database_schema: str | None = None  # None allows search_path MT isolation'
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def refactor_session():
    filepath = os.path.join(base_dir, "database", "session.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import text and Any
    if "from typing import AsyncGenerator" in content:
        content = content.replace("from typing import AsyncGenerator", "from typing import AsyncGenerator, Any\nfrom sqlalchemy import text")
    
    # Update get_session
    old_func = '''async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get a database session.
    
    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()'''
            
    new_func = '''async def get_session(ctx: Any = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get a tenant-aware database session.
    """
    tenant_schema = ctx.schema_name if ctx and hasattr(ctx, "schema_name") else "public"
    
    async with AsyncSessionLocal() as session:
        try:
            if "postgresql" in settings.intellicare_database_url:
                await session.execute(text(f"SET search_path TO {tenant_schema}"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            if "postgresql" in settings.intellicare_database_url:
                await session.execute(text("SET search_path TO public"))
            await session.close()'''
            
    content = content.replace(old_func, new_func)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def refactor_dependencies():
    filepath = os.path.join(base_dir, "api", "dependencies.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import context logic and Any
    import_stmt = "\nfrom typing import AsyncGenerator, Any\nfrom donabedian.api.auth import get_tenant_context, check_module_active\n"
    content = content.replace("from typing import AsyncGenerator\n", import_stmt)

    old_func = '''# Database session dependency (re-export for convenience)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for FastAPI routes.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    async for session in get_session():
        yield session'''

    new_func = '''# Database session dependency
async def get_db(
    ctx: Any = Depends(get_tenant_context),
    _check: Any = Depends(check_module_active('intellicare-donabedian'))
) -> AsyncGenerator[AsyncSession, None]:
    """Tenant-isolated database session."""
    async for session in get_session(ctx):
        yield session'''
        
    if "async def get_db() -> AsyncGenerator[AsyncSession, None]:" in content:
        content = re.sub(r'# Database session dependency.*?yield session', new_func, content, flags=re.DOTALL)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    create_auth_fallback()
    refactor_config()
    refactor_session()
    refactor_dependencies()
    print("Donabedian refatorado.")
