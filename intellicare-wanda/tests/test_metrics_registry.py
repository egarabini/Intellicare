"""Tests for metrics registry (EF-W010)."""

from wanda.observability import InMemorySLOHistoryStore, MetricsRegistry


def test_metrics_registry_render_and_summary() -> None:
    registry = MetricsRegistry()
    registry.record_orchestration("chat", "keyword", "success", 0.4)
    registry.record_orchestration("chat", "keyword", "failed", 1.2)
    registry.record_agent_call("intellicare-oswaldo", "analyze", "success", 0.2)
    registry.record_agent_call("intellicare-oswaldo", "analyze", "failed", 0.3)
    registry.record_routing_decision("keyword", 1, True)
    registry.record_routing_decision("llm", 2, True, llm_confidence=0.92)
    registry.record_circuit_transition("intellicare-oswaldo", "CLOSED", "OPEN")
    registry.record_ips_cache_hit("fresh", age_hours=1.5)
    registry.record_ips_cache_miss("expired")
    registry.record_ips_load(0.35)
    registry.record_alert_received("intellicare-zilda", "critical")
    registry.set_alerts_pending("critical", 1)
    registry.record_alert_ack("critical", 120)
    registry.record_alert_escalated("high")
    registry.record_workflow_execution("wf-renal", "success", duration_seconds=2.4, iterations=3)
    payload = registry.render().decode("utf-8")
    assert "wanda_orchestration_requests_total" in payload
    assert "wanda_agent_calls_total" in payload
    assert "wanda_routing_decisions_total" in payload
    assert "wanda_agent_response_duration_seconds" in payload
    assert "wanda_alert_acknowledgment_seconds" in payload
    assert "wanda_workflow_executions_total" in payload
    summary = registry.summary()
    assert summary["metrics_enabled"] is True
    assert "slos" in summary
    assert summary["slos"]["p95_latency_seconds"]["value"] is not None
    assert summary["slos"]["availability_ratio"]["value"] == 0.5
    assert summary["slos"]["critical_alert_ack_seconds"]["value"] == 120.0
    assert "intellicare-oswaldo" in summary["agents"]
    assert summary["ips_cache"]["hit_rate"] == 0.5
    assert summary["routing"]["llm_rate"] == 0.5
    assert summary["alerts"]["critical_pending"] == 1.0
    snapshot = registry.slos_snapshot()
    assert "timestamp" in snapshot
    history = registry.slos_history(limit=10)
    assert len(history) == 1


def test_metrics_registry_uses_persistent_history_store() -> None:
    store = InMemorySLOHistoryStore(max_items=20)
    first = MetricsRegistry(history_store=store, history_limit=20)
    first.record_orchestration("chat", "keyword", "success", 0.2)
    first.slos_snapshot()
    second = MetricsRegistry(history_store=store, history_limit=20)
    history = second.slos_history(limit=10)
    assert len(history) == 1
