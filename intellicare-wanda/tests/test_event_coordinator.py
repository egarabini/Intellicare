"""Tests for EventCoordinator and EventDeduplicator (EF-W006)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from wanda.events.models import IntelliCareEvent, EventCoordinationStatus
from wanda.events.deduplicator import EventDeduplicator
from wanda.events.coordinator import EventCoordinator, EVENT_COORDINATION_MAP


def make_event(**kwargs) -> IntelliCareEvent:
    defaults = {
        "event_type": "lab_result_critical",
        "patient_id": "p1",
        "source_module": "intellicare-florence",
    }
    defaults.update(kwargs)
    return IntelliCareEvent(**defaults)


# ── EventDeduplicator ─────────────────────────────────────────────

class TestEventDeduplicator:
    @pytest.mark.asyncio
    async def test_first_event_not_duplicate(self):
        dedup = EventDeduplicator()
        event = make_event()
        assert not await dedup.is_duplicate(event)

    @pytest.mark.asyncio
    async def test_mark_then_duplicate(self):
        dedup = EventDeduplicator()
        event = make_event()
        await dedup.mark_processed(event)
        assert await dedup.is_duplicate(event)

    @pytest.mark.asyncio
    async def test_different_events_not_duplicate(self):
        dedup = EventDeduplicator()
        e1 = make_event()
        e2 = make_event()  # different event_id (uuid4 by default)
        await dedup.mark_processed(e1)
        assert not await dedup.is_duplicate(e2)

    @pytest.mark.asyncio
    async def test_redis_fallback(self):
        redis_mock = AsyncMock()
        redis_mock.exists.side_effect = Exception("down")
        dedup = EventDeduplicator(redis_client=redis_mock)
        event = make_event()
        assert not await dedup.is_duplicate(event)

    @pytest.mark.asyncio
    async def test_mark_processed_with_redis(self):
        redis_mock = AsyncMock()
        redis_mock.set = AsyncMock(return_value=True)
        dedup = EventDeduplicator(redis_client=redis_mock)
        event = make_event()
        await dedup.mark_processed(event)
        redis_mock.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_processed_redis_error_fallback(self):
        redis_mock = AsyncMock()
        redis_mock.set = AsyncMock(side_effect=Exception("Redis down"))
        dedup = EventDeduplicator(redis_client=redis_mock)
        event = make_event()
        # Should not raise — falls back to in-memory set
        await dedup.mark_processed(event)
        assert dedup._key(event) in dedup._seen


# ── EVENT_COORDINATION_MAP ────────────────────────────────────────

class TestEventCoordinationMap:
    def test_all_6_event_types_present(self):
        expected = {
            "lab_result_critical", "vital_sign_alert", "adherence_missed",
            "condition_worsened", "medication_schedule", "appointment_reminder",
        }
        assert expected.issubset(set(EVENT_COORDINATION_MAP.keys()))

    def test_critical_events_have_workflow(self):
        assert EVENT_COORDINATION_MAP["lab_result_critical"]["workflow"] == "critical_alert"
        assert EVENT_COORDINATION_MAP["condition_worsened"]["workflow"] == "critical_alert"

    def test_low_priority_events_no_workflow(self):
        assert EVENT_COORDINATION_MAP["medication_schedule"]["workflow"] is None
        assert EVENT_COORDINATION_MAP["appointment_reminder"]["workflow"] is None

    def test_lab_critical_notifies_florence_and_oswaldo(self):
        agents = EVENT_COORDINATION_MAP["lab_result_critical"]["agents"]
        assert "intellicare-florence" in agents
        assert "intellicare-oswaldo" in agents


# ── EventCoordinator ─────────────────────────────────────────────

class TestEventCoordinator:
    @pytest.fixture
    def coordinator(self):
        return EventCoordinator()

    @pytest.mark.asyncio
    async def test_coordinate_unknown_type_skipped(self, coordinator):
        event = make_event(event_type="unknown_event_type")
        result = await coordinator.coordinate(event)
        assert result.status == EventCoordinationStatus.SKIPPED
        assert "desconhecido" in (result.error or "").lower()

    @pytest.mark.asyncio
    async def test_coordinate_dedup_skipped(self, coordinator):
        event = make_event()
        await coordinator._deduplicator.mark_processed(event)
        result = await coordinator.coordinate(event)
        assert result.status == EventCoordinationStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_coordinate_with_alert_hub(self):
        alert_hub = MagicMock()
        alert_hub.receive_alert = AsyncMock(return_value=MagicMock(status="accepted"))
        coordinator = EventCoordinator(alert_hub=alert_hub)
        event = make_event(event_type="vital_sign_alert")
        result = await coordinator.coordinate(event)
        assert result.status in (EventCoordinationStatus.SUCCESS, EventCoordinationStatus.PARTIAL)
        alert_hub.receive_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_coordinate_returns_result_fields(self, coordinator):
        event = make_event(event_type="medication_schedule")
        result = await coordinator.coordinate(event)
        assert result.event_id == event.event_id
        assert result.event_type == event.event_type
        assert hasattr(result, "coordination_time_ms")
        assert hasattr(result, "agents_notified")

    @pytest.mark.asyncio
    async def test_update_module_urls(self, coordinator):
        coordinator.update_module_urls({"intellicare-florence": "http://florence:8002"})
        assert coordinator._module_urls["intellicare-florence"] == "http://florence:8002"

    @pytest.mark.asyncio
    async def test_coordinate_with_workflow_executor(self):
        workflow_executor = MagicMock()
        workflow_executor.execute = AsyncMock(return_value=MagicMock(success=True))
        coordinator = EventCoordinator(workflow_executor=workflow_executor)
        event = make_event(event_type="lab_result_critical")
        result = await coordinator.coordinate(event)
        assert result.workflow_triggered == "critical_alert" or result.workflow_triggered is None
