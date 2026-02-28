"""IntelliCare Core — SDK compartilhado para modulos IntelliCare."""

__version__ = "1.0.0"

from intellicare_core.config.base import BaseModuleConfig
from intellicare_core.contracts.health import HealthCheck, DependencyStatus
from intellicare_core.contracts.module_info import ModuleInfo
from intellicare_core.contracts.base_agent import BaseAgent
from intellicare_core.tenant.context import TenantContext
from intellicare_core.tenant.session import TenantAwareSessionFactory
from intellicare_core.tenant.redis import TenantRedisClient

__all__ = [
    "BaseModuleConfig",
    "HealthCheck",
    "DependencyStatus",
    "ModuleInfo",
    "BaseAgent",
    "TenantContext",
    "TenantAwareSessionFactory",
    "TenantRedisClient",
]
