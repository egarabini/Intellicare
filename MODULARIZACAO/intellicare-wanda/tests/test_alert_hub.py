"""Tests for AlertHub pipeline (EF-W007)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from wanda.alerts.hub import AlertHub
from wanda.alerts.models import ClinicalAlert, AlertProcessingResult


def make_alert(**kwargs) -> ClinicalAlert:
    defaults = {
        "patient_id": "p1",
        "source_agent": "intellicare-oswaldo",
        "alert_type": "condition_worsened",
        "severity": "high",
        "title": "Creatinina elevada",
    }
    defaults.update(kwargs)
    return ClinicalAlert(**defaults)


@pytest.fixture
def hub():
    return AlertHub(consolidation_window_seconds=300, escalation_check_interval_seconds=999)


class TestAlertHubPipeline:
    @pytest.mark.asyncio
    async def test_receive_alert_accepted(self, hub):
        alert = make_alert()
        result = await hub.receive_alert(alert)
        assert result.status == "accepted"
        assert result.priority_score > 0
        assert result.alert_id == alert.alert_id

    @pytest.mark.asyncio
    async def test_receive_alert_dedup_on_second_call(self, hub):
        alert = make_alert()
        r1 = await hub.receive_alert(alert)
        assert r1.status == "accepted"
        # Same idempotency_key → duplicate
        r2 = await hub.receive_alert(alert)
        assert r2.status == "deduplicated"

    @pytest.mark.asyncio
    async def test_receive_alert_consolidated(self, hub):
        # Two alerts with same type/severity in consolidation window
        a1 = make_alert(alert_type="vital_sign", severity="medium")
        a2 = make_alert(alert_type="vital_sign", severity="medium")
        # Give them different idempotency keys
        a1.idempotency_key = "key-1"
        a2.idempotency_key = "key-2"
        r1 = await hub.receive_alert(a1)
        assert r1.status == "accepted"
        r2 = await hub.receive_alert(a2)
        assert r2.status == "consolidated"

    @pytest.mark.asyncio
    async def test_dispatch_callback_called(self, hub):
        callback = AsyncMock()
        hub._dispatch = callback
        alert = make_alert(severity="critical")
        result = await hub.receive_alert(alert)
        assert result.status == "accepted"
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_callback_error_handled(self, hub):
        async def failing_dispatch(alert, score):
            raise RuntimeError("dispatch failed")

        hub._dispatch = failing_dispatch
        alert = make_alert()
        result = await hub.receive_alert(alert)
        # Should still be accepted despite dispatch error
        assert result.status == "accepted"

    @pytest.mark.asyncio
    async def test_get_pending_alerts(self, hub):
        alert = make_alert()
        await hub.receive_alert(alert)
        pending = hub.get_pending_alerts()
        assert len(pending) == 1

    @pytest.mark.asyncio
    async def test_acknowledge_cancels_escalation(self, hub):
        alert = make_alert()
        await hub.receive_alert(alert)
        ok = hub.acknowledge_alert(alert.alert_id, "nurse-1")
        assert ok
        assert hub._escalator.pending_count == 0

    @pytest.mark.asyncio
    async def test_resolve_alert(self, hub):
        alert = make_alert()
        await hub.receive_alert(alert)
        ok = hub.resolve_alert(alert.alert_id, "dr-1", "Normalizado")
        assert ok

    @pytest.mark.asyncio
    async def test_get_stats(self, hub):
        alert = make_alert()
        await hub.receive_alert(alert)
        stats = hub.get_stats()
        assert "pending" in stats
        assert stats["pending"] >= 0

    @pytest.mark.asyncio
    async def test_severity_upgraded_by_context(self, hub):
        # medium + hospitalized + worsening + first_occurrence = 50+10+10+10 = 80 → no upgrade to critical
        alert = make_alert(
            severity="medium",
            clinical_data={"hospitalized": True, "worsening_trend": True, "first_occurrence": True}
        )
        result = await hub.receive_alert(alert)
        assert result.status == "accepted"
        assert result.priority_score >= 80

    @pytest.mark.asyncio
    async def test_start_stop(self, hub):
        await hub.start()
        assert hub._escalator._running
        await hub.stop()
        assert not hub._escalator._running

    @pytest.mark.asyncio
    async def test_metrics_are_recorded_for_receive_and_ack(self):
        metrics = MagicMock()
        hub = AlertHub(
            consolidation_window_seconds=300,
            escalation_check_interval_seconds=999,
            metrics_registry=metrics,
        )
        alert = make_alert(severity="critical")
        result = await hub.receive_alert(alert)
        assert result.status == "accepted"
        assert metrics.record_alert_received.called
        ok = hub.acknowledge_alert(alert.alert_id, "nurse-1")
        assert ok
        assert metrics.record_alert_ack.called
