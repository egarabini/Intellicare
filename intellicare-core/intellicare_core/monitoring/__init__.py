"""IntelliCare monitoring package.

Provides Prometheus metrics middleware and helpers for all modules.

Usage:
    from intellicare_core.monitoring.metrics import setup_metrics
    setup_metrics(app, module_name="florence")
"""

from intellicare_core.monitoring.metrics import (
    setup_metrics,
    set_module_health,
    record_tenant_failure,
)

__all__ = [
    "setup_metrics",
    "set_module_health",
    "record_tenant_failure",
]
