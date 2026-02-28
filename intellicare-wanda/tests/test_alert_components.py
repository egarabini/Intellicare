"""Tests for AlertDeduplicator, AlertPrioritizer, AlertConsolidator, AlertEscalator, AlertQueue (EF-W007)."""

import asyncio
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from wanda.alerts.models import AlertPriority, ClinicalAlert, ConsolidatedAlert
from wanda.alerts.deduplicator import AlertDeduplicator, DEDUP_WINDOWS
from wanda.alerts.prioritizer import AlertPrioritizer
from wanda.alerts.consolidator import AlertConsolidator
from wanda.alerts.escalator import AlertEscalator
from wanda.alerts.queue import AlertQueue


def make_alert(**kwargs) -> ClinicalAlert:
    defaults = {
        "patient_id": "p1",
        "source_agent": "intellicare-florence",
        "alert_type": "vital_sign",
        "severity": "high",
        "title": "Frequência cardíaca elevada",
    }
    defaults.update(kwargs)
    return ClinicalAlert(**defaults)


# ── Deduplicator ────────────────────────────────────────────────

class TestAlertDeduplicator:
    @pytest.mark.asyncio
    async def test_first_alert_not_duplicate(self):
        dedup = AlertDeduplicator()
        alert = make_alert()
        assert not await dedup.is_duplicate(alert)

    @pytest.mark.asyncio
    async def test_mark_then_is_duplicate(self):
        dedup = AlertDeduplicator()
        alert = make_alert()
        await dedup.mark_processed(alert)
        assert await dedup.is_duplicate(alert)

    @pytest.mark.asyncio
    async def test_different_alerts_not_duplicate(self):
        dedup = AlertDeduplicator()
        a1 = make_alert(alert_type="vital_sign")
        a2 = make_alert(alert_type="lab_result")
        await dedup.mark_processed(a1)
        assert not await dedup.is_duplicate(a2)

    def test_dedup_window_vital_sign(self):
        dedup = AlertDeduplicator()
        secs = dedup._window_seconds("vital_sign")
        assert secs == 600  # 10 min

    def test_dedup_window_lab_result(self):
        dedup = AlertDeduplicator()
        assert dedup._window_seconds("lab_result") == 3600  # 1h

    def test_dedup_window_default(self):
        dedup = AlertDeduplicator()
        assert dedup._window_seconds("unknown_type") == 3600  # default 1h

    @pytest.mark.asyncio
    async def test_redis_fallback_on_error(self):
        redis_mock = AsyncMock()
        redis_mock.exists.side_effect = Exception("connection refused")
        dedup = AlertDeduplicator(redis_client=redis_mock)
        alert = make_alert()
        # Should fall back to in-memory — first check: not duplicate
        assert not await dedup.is_duplicate(alert)

    @pytest.mark.asyncio
    async def test_redis_mark_fallback_on_error(self):
        redis_mock = AsyncMock()
        redis_mock.set.side_effect = Exception("connection refused")
        dedup = AlertDeduplicator(redis_client=redis_mock)
        alert = make_alert()
        await dedup.mark_processed(alert)
        # Should be in memory fallback
        assert await dedup.is_duplicate(alert)

    @pytest.mark.asyncio
    async def test_redis_mark_success(self):
        redis_mock = AsyncMock()
        redis_mock.set = AsyncMock(return_value=True)
        dedup = AlertDeduplicator(redis_client=redis_mock)
        alert = make_alert()
        await dedup.mark_processed(alert)
        redis_mock.set.assert_called_once()


# ── Prioritizer ────────────────────────────────────────────────

class TestAlertPrioritizer:
    @pytest.mark.asyncio
    async def test_critical_base_score(self):
        p = AlertPrioritizer()
        alert = make_alert(severity="critical")
        result = await p.calculate_priority(alert)
        assert result.score >= 90
        assert result.adjusted_severity == "critical"

    @pytest.mark.asyncio
    async def test_low_base_score(self):
        p = AlertPrioritizer()
        alert = make_alert(severity="low")
        result = await p.calculate_priority(alert)
        assert result.score == 25
        assert result.adjusted_severity == "low"

    @pytest.mark.asyncio
    async def test_hospitalized_adds_10(self):
        p = AlertPrioritizer()
        alert = make_alert(severity="medium", clinical_data={"hospitalized": True})
        result = await p.calculate_priority(alert)
        assert result.score >= 60  # 50 + 10
        assert "paciente internado" in result.factors

    @pytest.mark.asyncio
    async def test_worsening_trend_adds_10(self):
        p = AlertPrioritizer()
        alert = make_alert(severity="medium", clinical_data={"worsening_trend": True})
        result = await p.calculate_priority(alert)
        assert result.score >= 60
        assert "tendencia de piora" in result.factors

    @pytest.mark.asyncio
    async def test_recurring_unresolved_subtracts_10(self):
        p = AlertPrioritizer()
        alert = make_alert(severity="medium", clinical_data={"recurring_unresolved": True})
        result = await p.calculate_priority(alert)
        assert result.score == 40  # 50 - 10

    @pytest.mark.asyncio
    async def test_high_risk_flag_adds_5(self):
        p = AlertPrioritizer()
        alert = make_alert(severity="medium", clinical_data={"high_risk": True})
        result = await p.calculate_priority(alert)
        assert result.score == 55

    @pytest.mark.asyncio
    async def test_score_capped_at_100(self):
        p = AlertPrioritizer()
        alert = make_alert(
            severity="critical",
            clinical_data={"hospitalized": True, "worsening_trend": True, "first_occurrence": True, "high_risk": True},
        )
        result = await p.calculate_priority(alert)
        assert result.score <= 100

    @pytest.mark.asyncio
    async def test_severity_upgrade_to_critical(self):
        p = AlertPrioritizer()
        # high=70 + hospitalized=10 + worsening=10 = 90 → upgrade to critical
        alert = make_alert(
            severity="high",
            clinical_data={"hospitalized": True, "worsening_trend": True},
        )
        result = await p.calculate_priority(alert)
        assert result.adjusted_severity == "critical"
        assert "escalada" in " ".join(result.factors).lower()

    @pytest.mark.asyncio
    async def test_patient_context_hospitalized(self):
        p = AlertPrioritizer()
        alert = make_alert(severity="medium")
        result = await p.calculate_priority(alert, patient_context={"hospitalized": True})
        assert result.score >= 60


# ── Consolidator ────────────────────────────────────────────────

class TestAlertConsolidator:
    def test_first_alert_starts_window(self):
        c = AlertConsolidator(window_seconds=300)
        alert = make_alert()
        result = c.try_consolidate(alert)
        assert result is None  # first alert → starts window, not consolidated

    def test_second_alert_consolidates(self):
        c = AlertConsolidator(window_seconds=300)
        a1 = make_alert(alert_type="vital_sign", severity="high")
        a2 = make_alert(alert_type="vital_sign", severity="high")
        c.try_consolidate(a1)
        result = c.try_consolidate(a2)
        assert result is not None
        assert isinstance(result, ConsolidatedAlert)
        assert result.primary_alert.alert_id == a1.alert_id

    def test_different_type_not_consolidated(self):
        c = AlertConsolidator(window_seconds=300)
        a1 = make_alert(alert_type="vital_sign")
        a2 = make_alert(alert_type="lab_result")
        c.try_consolidate(a1)
        result = c.try_consolidate(a2)
        assert result is None  # different type → new window

    def test_consolidated_title_contains_count(self):
        a1 = make_alert(title="HR elevado")
        a2 = make_alert(title="HR elevado")
        ca = ConsolidatedAlert(primary_alert=a1, merged_ids=[a2.alert_id])
        assert "(+1 relacionados)" in ca.consolidated_title


# ── Escalator ────────────────────────────────────────────────

class TestAlertEscalator:
    @pytest.mark.asyncio
    async def test_schedule_returns_escalate_at(self):
        escalator = AlertEscalator(check_interval_seconds=999)
        cb = AsyncMock()
        escalate_at = escalator.schedule("alert-1", "critical", cb)
        assert escalate_at is not None
        assert escalator.pending_count == 1

    @pytest.mark.asyncio
    async def test_cancel_removes_from_pending(self):
        escalator = AlertEscalator()
        cb = AsyncMock()
        escalator.schedule("alert-2", "high", cb)
        escalator.cancel("alert-2")
        assert escalator.pending_count == 0

    @pytest.mark.asyncio
    async def test_start_stop(self):
        escalator = AlertEscalator(check_interval_seconds=999)
        await escalator.start()
        assert escalator._running
        await escalator.stop()
        assert not escalator._running


# ── Queue ────────────────────────────────────────────────

class TestAlertQueue:
    def test_enqueue_and_get_pending(self):
        q = AlertQueue()
        q.enqueue("a1", "p1", "high", 80, "Teste", "florence", "vital_sign")
        pending = q.get_pending()
        assert len(pending) == 1
        assert pending[0]["alert_id"] == "a1"

    def test_get_pending_sorted_by_score(self):
        q = AlertQueue()
        q.enqueue("a1", "p1", "low", 30, "Low", "florence", "vital_sign")
        q.enqueue("a2", "p1", "high", 80, "High", "florence", "vital_sign")
        pending = q.get_pending()
        assert pending[0]["priority_score"] == 80

    def test_acknowledge(self):
        q = AlertQueue()
        q.enqueue("a1", "p1", "high", 80, "Test", "florence", "vital_sign")
        ok = q.acknowledge("a1", "nurse-1")
        assert ok
        assert q._memory["a1"]["status"] == "acknowledged"
        assert q._memory["a1"]["acknowledged_by"] == "nurse-1"

    def test_acknowledge_unknown_returns_false(self):
        q = AlertQueue()
        assert not q.acknowledge("unknown-id", "nurse")

    def test_resolve(self):
        q = AlertQueue()
        q.enqueue("a1", "p1", "medium", 50, "Test", "florence", "lab_result")
        ok = q.resolve("a1", "dr-1", "Resolvido por exame normal")
        assert ok
        assert q._memory["a1"]["status"] == "resolved"

    def test_filter_by_patient(self):
        q = AlertQueue()
        q.enqueue("a1", "p1", "high", 80, "T1", "f", "v")
        q.enqueue("a2", "p2", "high", 80, "T2", "f", "v")
        pending = q.get_pending(patient_id="p1")
        assert len(pending) == 1
        assert pending[0]["patient_id"] == "p1"

    def test_get_stats(self):
        q = AlertQueue()
        q.enqueue("a1", "p1", "high", 80, "T", "f", "v")
        q.acknowledge("a1", "user")
        stats = q.get_stats()
        assert stats["acknowledged"] == 1
        assert stats["pending"] == 0
