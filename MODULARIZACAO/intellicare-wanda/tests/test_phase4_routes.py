"""Tests for phase 4 routes (resilience, traces, metrics)."""

from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from wanda.api.metrics_routes import init_metrics_routes, router as metrics_router
from wanda.api.resilience_routes import init_resilience_routes, router as resilience_router
from wanda.api.trace_routes import init_trace_routes, router as trace_router
from wanda.observability import DecisionTrace, InMemoryTraceStore, MetricsRegistry
from wanda.resilience import CircuitBreakerManager, HealthDashboard


def test_resilience_routes_work_when_initialized() -> None:
    app = FastAPI()
    app.include_router(resilience_router)
    manager = CircuitBreakerManager()
    dashboard = HealthDashboard(manager)
    init_resilience_routes(health_dashboard=dashboard, circuit_breaker_manager=manager)
    client = TestClient(app)

    ecosystem = client.get("/api/v1/health/ecosystem")
    assert ecosystem.status_code == 200
    assert "overall" in ecosystem.json()

    missing = client.post("/api/v1/circuit/intellicare-oswaldo/reset")
    assert missing.status_code == 404


def test_trace_routes_require_init_and_then_return_data() -> None:
    app = FastAPI()
    app.include_router(trace_router)
    client = TestClient(app)
    assert client.get("/api/v1/traces").status_code == 503

    store = InMemoryTraceStore()
    init_trace_routes(store)
    ok = client.get("/api/v1/traces")
    assert ok.status_code == 200
    assert ok.json()["total"] == 0

    trace = DecisionTrace(
        trace_id="trace-1",
        original_query="dor no peito",
        patient_id="p-1",
        routing_method="keyword",
        success=True,
        total_latency_ms=120,
        created_at=datetime.utcnow(),
    )
    asyncio.run(store.save(trace))

    patterns = client.get("/api/v1/traces/patterns")
    assert patterns.status_code == 200
    assert "routing_methods" in patterns.json()

    anomalies = client.get("/api/v1/traces/anomalies")
    assert anomalies.status_code == 200
    assert "items" in anomalies.json()

    fhir = client.get(f"/api/v1/traces/{trace.trace_id}/fhir")
    assert fhir.status_code == 200
    assert fhir.json()["resourceType"] == "AuditEvent"


def test_metrics_routes_return_prometheus_payload() -> None:
    app = FastAPI()
    app.include_router(metrics_router)
    metrics = MetricsRegistry()
    init_metrics_routes(metrics)
    client = TestClient(app)

    text = client.get("/metrics")
    assert text.status_code == 200
    assert "wanda_orchestration_requests_total" in text.text
    summary = client.get("/api/v1/metrics/summary")
    assert summary.status_code == 200
    slos = client.get("/api/v1/slos")
    assert slos.status_code == 200
    history = client.get("/api/v1/slos/history")
    assert history.status_code == 200
