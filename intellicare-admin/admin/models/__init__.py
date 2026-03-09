from admin.db import Base
from .tenant import Tenant
from .plan import Plan
from .billing import BillingRecord
from .audit import GlobalAuditLog
from .tenant_gestor import TenantGestor
from .tenant_contrato import TenantContrato
from .estabelecimento import Estabelecimento
from .secretaria import Secretaria
from .module_test_log import ModuleTestLog

# Export Base so Alembic can import admin.models.Base
__all__ = [
    "Base",
    "Tenant",
    "Plan",
    "BillingRecord",
    "GlobalAuditLog",
    "TenantGestor",
    "TenantContrato",
    "Estabelecimento",
    "Secretaria",
    "ModuleTestLog",
]
