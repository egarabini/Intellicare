import os
import re

base_dir = r"c:\Users\egara\INTELLICARE\intellicare-grahame\grahame"

def create_auth_fallback():
    auth_code = '''"""Módulo de integração de autenticação e multitenancy para Grahame."""

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
            self.schema_name = f"tenant_{tenant_id}" if tenant_id and tenant_id != "default" else "public"
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


def refactor_deps():
    filepath = os.path.join(base_dir, "api", "deps.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = '''"""Dependências FastAPI do Grahame."""

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
'''
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)


def refactor_hl7v2_auth():
    filepath = os.path.join(base_dir, "api", "dependencies", "hl7v2_auth.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "from grahame.api.auth import get_tenant_context" not in content:
        content = content.replace("from fastapi import Depends, HTTPException, Request, Security", 
                                  "from fastapi import Depends, HTTPException, Request, Security\nfrom grahame.api.auth import get_tenant_context\nfrom sqlalchemy import text\nfrom typing import Any")

    old_func = """async def get_db_session(request: Request):
    \"\"\"
    Fornece sessão de banco ligada ao tempo de vida do request.
    Cria a factory se não existir (ex: em testes onde o lifespan foi by-passado).
    \"\"\"
    # Verifica app state
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        # Fallback de emergência (não recomendado para PROD, mas salva testes)
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        from grahame.config import config

        engine = create_async_engine(
            config.grahame_database_url or "sqlite+aiosqlite:///:memory:",
            echo=False,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        request.app.state.session_factory = session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise"""

    new_func = """async def get_db_session(request: Request, ctx: Any = Depends(get_tenant_context)):
    \"\"\"
    Fornece sessão de banco ligada ao tempo de vida do request isolada por tenant.
    \"\"\"
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from grahame.config import config
        engine = create_async_engine(
            config.grahame_database_url or "sqlite+aiosqlite:///:memory:",
            echo=False,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        request.app.state.session_factory = session_factory
        
    tenant_schema = ctx.schema_name if ctx and hasattr(ctx, "schema_name") else "public"
    async with session_factory() as session:
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
                await session.execute(text("SET search_path TO public"))"""
    
    content = content.replace(old_func, new_func)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def replace_direct_session_factory(route_file):
    filepath = os.path.join(base_dir, "api", "routes", route_file)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import get_tenant_session_context
    if "get_tenant_session_context" not in content:
        if "from grahame.api.deps import" in content:
            content = content.replace("from grahame.api.deps import", "from grahame.api.deps import get_tenant_session_context,")
        else:
            content = "from grahame.api.deps import get_tenant_session_context\n" + content

    # Patterns to replace
    p1 = "session = request.app.state.session_factory()\n    async with session:"
    p2 = "session = request.app.state.session_factory()\n        async with session:"
    
    r1 = "async with get_tenant_session_context(request) as session:"
    r2 = "async with get_tenant_session_context(request) as session:"

    content = content.replace(p1, r1)
    # the second pattern has 4 extra spaces of indentation
    content = content.replace("    session = request.app.state.session_factory()\n    async with session:", "    async with get_tenant_session_context(request) as session:")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    create_auth_fallback()
    refactor_deps()
    try:
        refactor_hl7v2_auth()
    except Exception as e:
        print(f"Error hl7v2_auth: {e}")
    try:
        replace_direct_session_factory("bot_routes.py")
        replace_direct_session_factory("subscription_routes.py")
    except Exception as e:
        print(f"Error direct session: {e}")
    print("Grahame refatorado.")
