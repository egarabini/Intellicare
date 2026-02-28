"""Contratos padrao para modulos IntelliCare."""

from intellicare_core.contracts.base_agent import BaseAgent
from intellicare_core.contracts.health import DependencyStatus, HealthCheck
from intellicare_core.contracts.module_info import ModuleInfo

__all__ = ["BaseAgent", "DependencyStatus", "HealthCheck", "ModuleInfo"]
