import os
import shutil

base_dir = r"c:\Users\egara\INTELLICARE\intellicare-oswaldo\oswaldo"

def create_auth_fallback():
    auth_code = '''"""Módulo de integração de autenticação e multitenancy para Oswaldo."""

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


def copy_tenant_utils():
    src = r"c:\Users\egara\INTELLICARE\intellicare-comunicacao\comunicacao\storage\tenant_utils.py"
    dst = os.path.join(base_dir, "datastore", "tenant_utils.py")
    if os.path.exists(src):
        shutil.copy(src, dst)
        return True
    return False


def refactor_fhir_datastore():
    filepath = os.path.join(base_dir, "datastore", "fhir_datastore.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import
    import_stmt = "from oswaldo.datastore.tenant_utils import get_tenant_conn\n"
    if import_stmt not in content:
        content = content.replace("from sqlalchemy import create_engine, text\n", import_stmt + "from sqlalchemy import create_engine, text\n")

    # Replace methods signature
    content = content.replace("def ensure_schema(self) -> None:", "def ensure_schema(self, ctx: Any = None) -> None:")
    content = content.replace("def reset(self) -> None:", "def reset(self, ctx: Any = None) -> None:")
    content = content.replace("def get_resource_by_type(self, resource_type: str, resource_id: str) -> dict[str, Any] | None:", "def get_resource_by_type(self, resource_type: str, resource_id: str, ctx: Any = None) -> dict[str, Any] | None:")
    content = content.replace("def list_resources(self, resource_type: str) -> list[dict[str, Any]]:", "def list_resources(self, resource_type: str, ctx: Any = None) -> list[dict[str, Any]]:")
    content = content.replace("descending: bool = True,\n    ) -> list[dict[str, Any]]:", "descending: bool = True,\n        ctx: Any = None,\n    ) -> list[dict[str, Any]]:")
    content = content.replace("def save_resource(self, resource: dict[str, Any]) -> str:", "def save_resource(self, resource: dict[str, Any], ctx: Any = None) -> str:")
    content = content.replace("def save_many(self, resources: Iterable[dict[str, Any]]) -> list[str]:", "def save_many(self, resources: Iterable[dict[str, Any]], ctx: Any = None) -> list[str]:")

    # Pass ctx recursively inside class where required 
    content = content.replace("return [self.save_resource(r) for r in resources]", "return [self.save_resource(r, ctx=ctx) for r in resources]")

    # Replace self._engine.begin() with get_tenant_conn
    content = content.replace("with self._engine.begin() as conn:", "with get_tenant_conn(self._engine, ctx) as conn:")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def refactor_engine():
    filepath = os.path.join(base_dir, "engine", "core_logic.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Signatures
    content = content.replace("patient_id: str, disease_id: str) -> StagingResult:", "patient_id: str, disease_id: str, ctx: Any = None) -> StagingResult:")
    content = content.replace("patient_id: str, disease_id: str) -> dict[str, Any]:", "patient_id: str, disease_id: str, ctx: Any = None) -> dict[str, Any]:")
    content = content.replace("patient_id: str, disease_id: str, staging: StagingResult, trends: dict[str, Any]) -> list[OswaldoAlert]:", "patient_id: str, disease_id: str, staging: StagingResult, trends: dict[str, Any], ctx: Any = None) -> list[OswaldoAlert]:")
    content = content.replace("patient_id: str, diseases: list[str] | None = None) -> OswaldoPatientSummary:", "patient_id: str, diseases: list[str] | None = None, ctx: Any = None) -> OswaldoPatientSummary:")
    content = content.replace("def _get_observations_for_profile(self, patient_id: str, disease_id: str) -> dict[str, list[dict[str, Any]]]:", "def _get_observations_for_profile(self, patient_id: str, disease_id: str, ctx: Any = None) -> dict[str, list[dict[str, Any]]]:")

    # Injections
    content = content.replace('observations = self._get_observations_for_profile(patient_id, disease_id)', 'observations = self._get_observations_for_profile(patient_id, disease_id, ctx=ctx)')
    content = content.replace('staging = self.calculate_staging(patient_id, disease_id)', 'staging = self.calculate_staging(patient_id, disease_id, ctx=ctx)')
    content = content.replace('trends = self.calculate_trends(patient_id, disease_id)', 'trends = self.calculate_trends(patient_id, disease_id, ctx=ctx)')
    content = content.replace('alerts = self.generate_alerts(patient_id, disease_id, staging, trends)', 'alerts = self.generate_alerts(patient_id, disease_id, staging, trends, ctx=ctx)')
    
    # Datastore calls
    content = content.replace('self._datastore.search_resources(\n            "Observation"', 'self._datastore.search_resources(\n            "Observation", ctx=ctx')
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def refactor_app():
    filepath = os.path.join(base_dir, "api", "app.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import
    import_stmt = "\nfrom fastapi import Depends\nfrom oswaldo.api.auth import get_tenant_context, check_module_active\n"
    content = content.replace("from fastapi import FastAPI\n", import_stmt + "from fastapi import FastAPI\n")

    depends_str = ", ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))"

    content = content.replace("async def health() -> dict[str, Any]:", f"async def health(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> dict[str, Any]:")
    content = content.replace("async def info() -> dict[str, Any]:", f"async def info(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> dict[str, Any]:")
    content = content.replace("async def list_diseases() -> list[dict[str, Any]]:", f"async def list_diseases(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> list[dict[str, Any]]:")
    
    content = content.replace("async def get_staging(patient_id: str, disease: str | None = None) -> dict[str, Any]:", f"async def get_staging(patient_id: str, disease: str | None = None{depends_str}) -> dict[str, Any]:")
    content = content.replace("async def get_alerts(patient_id: str) -> dict[str, Any]:", f"async def get_alerts(patient_id: str{depends_str}) -> dict[str, Any]:")
    content = content.replace("async def analyze(patient_id: str, diseases: list[str] | None = None) -> dict[str, Any]:", f"async def analyze(patient_id: str, diseases: list[str] | None = None{depends_str}) -> dict[str, Any]:")

    # Passing ctx
    content = content.replace("result = engine.calculate_staging(patient_id, disease)", "result = engine.calculate_staging(patient_id, disease, ctx=ctx)")
    content = content.replace("results[disease_id] = engine.calculate_staging(patient_id, disease_id).to_dict()", "results[disease_id] = engine.calculate_staging(patient_id, disease_id, ctx=ctx).to_dict()")
    
    content = content.replace("staging = engine.calculate_staging(patient_id, disease_id)", "staging = engine.calculate_staging(patient_id, disease_id, ctx=ctx)")
    content = content.replace("trends = engine.calculate_trends(patient_id, disease_id)", "trends = engine.calculate_trends(patient_id, disease_id, ctx=ctx)")
    content = content.replace("alerts = engine.generate_alerts(patient_id, disease_id, staging, trends)", "alerts = engine.generate_alerts(patient_id, disease_id, staging, trends, ctx=ctx)")
    
    content = content.replace("summary = engine.get_patient_summary(patient_id, diseases)", "summary = engine.get_patient_summary(patient_id, diseases, ctx=ctx)")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    create_auth_fallback()
    if copy_tenant_utils():
        refactor_fhir_datastore()
        refactor_engine()
        refactor_app()
        print("Refatoração de Oswaldo concluida.")
    else:
        print("Faltou o arquivo tenant_utils.py na origem.")
