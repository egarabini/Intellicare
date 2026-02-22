"""Tests for decision tracing (EF-W009)."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from wanda.observability import (
    AgentCallTrace,
    DecisionTrace,
    DecisionTracer,
    FHIRAuditExporter,
    InMemoryTraceStore,
    TraceQueryService,
)


@pytest.mark.asyncio
async def test_decision_tracer_lifecycle() -> None:
    store = InMemoryTraceStore()
    tracer = DecisionTracer(store)

    ctx = await tracer.start_trace(query="como esta o paciente", patient_id="p-1")
    await tracer.record_routing(ctx, routing_method="llm", reasoning="multi-agent")
    await tracer.record_agent_call(
        ctx,
        agent_name="intellicare-oswaldo",
        endpoint="/api/v1/analyze",
        payload={"patient_id": "p-1"},
        status_code=200,
        latency_ms=120,
        success=True,
    )
    trace = await tracer.complete_trace(ctx, success=True)

    assert trace.routing_method == "llm"
    assert trace.success is True
    assert len(trace.agent_calls) == 1
    assert trace.agent_calls[0].request_payload_hash

    loaded = await store.get(trace.trace_id)
    assert loaded is not None
    assert loaded.trace_id == trace.trace_id


@pytest.mark.asyncio
async def test_trace_store_search_filters() -> None:
    store = InMemoryTraceStore()
    tracer = DecisionTracer(store)

    ctx1 = await tracer.start_trace("q1", "p1")
    await tracer.record_routing(ctx1, "keyword")
    await tracer.complete_trace(ctx1, success=True)

    ctx2 = await tracer.start_trace("q2", "p2")
    await tracer.record_routing(ctx2, "llm")
    await tracer.record_agent_call(
        ctx2,
        agent_name="intellicare-florence",
        endpoint="/api/v1/analyze",
        payload={},
        status_code=500,
        latency_ms=90,
        success=False,
        error="down",
    )
    await tracer.complete_trace(ctx2, success=False)

    failed = await store.search(success=False)
    assert len(failed) == 1
    assert failed[0].original_query == "q2"

    by_agent = await store.search(agent="intellicare-florence")
    assert len(by_agent) == 1


@pytest.mark.asyncio
async def test_trace_query_service_and_fhir_export() -> None:
    store = InMemoryTraceStore()
    tracer = DecisionTracer(store)
    query_service = TraceQueryService(store)
    exporter = FHIRAuditExporter()

    ctx = await tracer.start_trace("q-lenta", "p9")
    await tracer.record_routing(ctx, "llm", reasoning="context-rich")
    trace = await tracer.complete_trace(ctx, success=False)
    trace.total_latency_ms = 6000
    await store.save(trace)

    patterns = await query_service.analyze_routing_patterns(period_days=7)
    assert patterns["total_traces"] == 1
    assert "llm" in patterns["routing_methods"]

    anomalies = await query_service.find_anomalies(period_days=7)
    assert any(item["type"] == "high_failure_rate" for item in anomalies)

    audit = await exporter.export_decision(trace)
    assert audit["resourceType"] == "AuditEvent"


@pytest.mark.asyncio
async def test_trace_query_service_detects_agent_error_spike() -> None:
    store = InMemoryTraceStore()
    query_service = TraceQueryService(store)
    now = datetime.utcnow()
    for idx in range(6):
        trace = DecisionTrace(
            trace_id=f"t-{idx}",
            original_query="q",
            patient_id=None,
            routing_method="keyword",
            success=False,
            total_latency_ms=200,
            created_at=now - timedelta(hours=1),
        )
        trace.agent_calls.append(
            AgentCallTrace(
                agent_name="intellicare-oswaldo",
                endpoint="/api/v1/analyze",
                status_code=500,
                latency_ms=100,
                success=False,
                error="err",
                request_payload_hash="x",
            )
        )
        await store.save(trace)

    anomalies = await query_service.find_anomalies(period_days=1)
    assert any(item["type"] == "agent_error_spike" for item in anomalies)
