"""Prometheus metrics middleware para módulos IntelliCare.

Expõe /metrics com métricas padrão de requisição HTTP + métricas
de tenant para suportar alertas multi-tenancy.

Uso no app.py de cada módulo:
    from intellicare_core.monitoring.metrics import setup_metrics

    app = create_app()
    setup_metrics(app, module_name="florence")
"""

from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# ── Metrics definitions (only created once) ─────────────────────────────

_metrics_initialized = False

_request_counter = None
_request_duration = None
_request_in_progress = None
_module_health = None
_tenant_requests = None
_tenant_resolution_failures = None


def _init_metrics() -> None:
    """Initialize Prometheus metrics (idempotent)."""
    global _metrics_initialized
    global _request_counter, _request_duration, _request_in_progress
    global _module_health, _tenant_requests, _tenant_resolution_failures

    if _metrics_initialized or not PROMETHEUS_AVAILABLE:
        return

    _request_counter = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status", "module"],
    )

    _request_duration = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint", "module"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )

    _request_in_progress = Gauge(
        "http_requests_in_progress",
        "Number of requests currently being processed",
        ["module"],
    )

    _module_health = Gauge(
        "intellicare_module_health_status",
        "Module health status (1=healthy, 0=unhealthy)",
        ["module"],
    )

    _tenant_requests = Counter(
        "tenant_requests_total",
        "Total requests per tenant",
        ["tenant_id", "module"],
    )

    _tenant_resolution_failures = Counter(
        "tenant_resolution_failures_total",
        "Total tenant resolution failures",
        ["module", "source"],
    )

    _metrics_initialized = True


# ── Middleware ───────────────────────────────────────────────────────────

class MetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that records request metrics."""

    def __init__(self, app, module_name: str = "unknown"):
        super().__init__(app)
        self.module_name = module_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not PROMETHEUS_AVAILABLE or not _metrics_initialized:
            return await call_next(request)

        method = request.method
        path = self._normalize_path(request.url.path)

        _request_in_progress.labels(module=self.module_name).inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            _request_counter.labels(
                method=method,
                endpoint=path,
                status=status,
                module=self.module_name,
            ).inc()
            _request_duration.labels(
                method=method,
                endpoint=path,
                module=self.module_name,
            ).observe(duration)
            _request_in_progress.labels(module=self.module_name).dec()

            # Track tenant if present
            tenant_id = getattr(request.state, "tenant_id", None) if hasattr(request, "state") else None
            if tenant_id:
                _tenant_requests.labels(
                    tenant_id=tenant_id,
                    module=self.module_name,
                ).inc()

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize URL paths to reduce metric cardinality."""
        parts = path.strip("/").split("/")
        normalized = []
        for i, part in enumerate(parts):
            if i >= 3 and not part.startswith("api"):
                if any(c.isdigit() for c in part) or len(part) > 20:
                    normalized.append("{id}")
                    continue
            normalized.append(part)
        return "/" + "/".join(normalized)


# ── Public API ───────────────────────────────────────────────────────────

def setup_metrics(app: FastAPI, module_name: str) -> None:
    """Configure Prometheus metrics for a FastAPI app.

    Adds MetricsMiddleware, /metrics endpoint, and sets health gauge.
    """
    if not PROMETHEUS_AVAILABLE:
        import logging
        logging.getLogger(__name__).warning(
            "prometheus_client not installed — metrics disabled"
        )
        return

    _init_metrics()

    app.add_middleware(MetricsMiddleware, module_name=module_name)
    _module_health.labels(module=module_name).set(1)

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


def set_module_health(module_name: str, healthy: bool) -> None:
    """Update module health gauge."""
    if _module_health:
        _module_health.labels(module=module_name).set(1 if healthy else 0)


def record_tenant_failure(module_name: str, source: str = "unknown") -> None:
    """Increment tenant resolution failure counter."""
    if _tenant_resolution_failures:
        _tenant_resolution_failures.labels(module=module_name, source=source).inc()
