import os

base_dir = r"c:\Users\egara\INTELLICARE\intellicare-florence\florence"

def create_auth_fallback():
    auth_code = '''"""Módulo de integração de autenticação e multitenancy para Florence."""

import logging
from typing import Any

from fastapi import Depends, Header

try:
    from intellicare_auth.tenant.context import TenantContext, get_tenant_context
    from intellicare_auth.fastapi.middleware import check_module_active
    _HAS_AUTH = True
except ImportError:
    import json
    _HAS_AUTH = False

logger = logging.getLogger(__name__)


if not _HAS_AUTH:
    class MockTenantContext:
        """Contexto de tenant local para fallback."""

        def __init__(self, tenant_id: str, tenant_name: str = "Local Tenant"):
            self.tenant_id = tenant_id
            self.tenant_name = tenant_name
            self.schema_name = f"tenant_{tenant_id}"
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

def refactor_app():
    filepath = os.path.join(base_dir, "api", "app.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import
    import_stmt = "\nfrom fastapi import Depends\nfrom florence.api.auth import get_tenant_context, check_module_active\n"
    content = content.replace("from fastapi import FastAPI\n", import_stmt + "from fastapi import FastAPI\n")

    depends_str = ", ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-florence'))"

    content = content.replace("async def health() -> dict[str, Any]:", "async def health(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-florence'))) -> dict[str, Any]:")
    content = content.replace("async def info() -> dict[str, Any]:", "async def info(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-florence'))) -> dict[str, Any]:")
    content = content.replace("async def list_panels() -> list[dict[str, Any]]:", "async def list_panels(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-florence'))) -> list[dict[str, Any]]:")
    content = content.replace("async def list_labs() -> list[dict[str, Any]]:", "async def list_labs(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-florence'))) -> list[dict[str, Any]]:")
    content = content.replace("async def list_protocols() -> dict[str, Any]:", "async def list_protocols(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-florence'))) -> dict[str, Any]:")

    content = content.replace("async def interpret_labs(request: LabResultsRequest) -> dict[str, Any]:", f"async def interpret_labs(request: LabResultsRequest{depends_str}) -> dict[str, Any]:")
    content = content.replace("async def analyze(request: AnalyzeRequest) -> dict[str, Any]:", f"async def analyze(request: AnalyzeRequest{depends_str}) -> dict[str, Any]:")
    content = content.replace("async def analyze_with_rag(request: AnalyzeWithRAGRequest) -> dict[str, Any]:", f"async def analyze_with_rag(request: AnalyzeWithRAGRequest{depends_str}) -> dict[str, Any]:")
    content = content.replace("async def rag_query(request: RAGQueryRequest) -> dict[str, Any]:", f"async def rag_query(request: RAGQueryRequest{depends_str}) -> dict[str, Any]:")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    create_auth_fallback()
    refactor_app()
    print("Florence refatorado.")
