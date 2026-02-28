"""Tests for EcosystemEventConsumer (EF-W006)."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from wanda.events.consumer import EcosystemEventConsumer, INTELLICARE_STREAMS
from wanda.events.coordinator import EventCoordinator
from wanda.events.models import IntelliCareEvent, EventCoordinationStatus


@pytest.fixture
def coordinator():
    c = MagicMock(spec=EventCoordinator)
    c.coordinate = AsyncMock(return_value=MagicMock(
        status=EventCoordinationStatus.SUCCESS,
        event_id="e1",
        agents_notified=["florence"],
    ))
    return c


@pytest.fixture
def redis_mock():
    r = AsyncMock()
    r.xgroup_create = AsyncMock(return_value=True)
    r.xreadgroup = AsyncMock(return_value=[])
    r.xack = AsyncMock()
    return r


class TestEcosystemEventConsumer:
    def test_status_not_running(self, coordinator):
        consumer = EcosystemEventConsumer(redis_client=None, coordinator=coordinator)
        status = consumer.status
        assert status["running"] is False
        assert status["processed"] == 0
        assert status["errors"] == 0

    def test_streams_list(self, coordinator):
        consumer = EcosystemEventConsumer(redis_client=None, coordinator=coordinator)
        status = consumer.status
        assert len(status["streams"]) == 4
        assert "intellicare:events:lab" in status["streams"]

    @pytest.mark.asyncio
    async def test_start_consuming_no_redis(self, coordinator):
        consumer = EcosystemEventConsumer(redis_client=None, coordinator=coordinator)
        await consumer.start_consuming()
        assert not consumer._running  # no Redis → stays disabled

    @pytest.mark.asyncio
    async def test_start_consuming_with_redis(self, coordinator, redis_mock):
        consumer = EcosystemEventConsumer(redis_client=redis_mock, coordinator=coordinator)
        await consumer.start_consuming()
        assert consumer._running
        await consumer.stop_consuming()
        assert not consumer._running

    @pytest.mark.asyncio
    async def test_stop_consuming_idempotent(self, coordinator):
        consumer = EcosystemEventConsumer(redis_client=None, coordinator=coordinator)
        await consumer.stop_consuming()  # Should not raise even if not started

    @pytest.mark.asyncio
    async def test_handle_message_calls_coordinator(self, coordinator, redis_mock):
        consumer = EcosystemEventConsumer(
            redis_client=redis_mock, coordinator=coordinator, group="wanda"
        )
        data = {
            "event_type": "lab_result_critical",
            "patient_id": "p1",
            "source_module": "intellicare-florence",
            "payload": json.dumps({"hba1c": 9.5}),
            "priority": "critical",
        }
        await consumer._handle_message("intellicare:events:lab", "1-0", data)
        coordinator.coordinate.assert_called_once()
        redis_mock.xack.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_message_coordinator_error(self, coordinator, redis_mock):
        coordinator.coordinate.side_effect = Exception("coordinator failed")
        consumer = EcosystemEventConsumer(redis_client=redis_mock, coordinator=coordinator)
        data = {"patient_id": "p1", "source_module": "test"}
        await consumer._handle_message("intellicare:events:vitals", "1-0", data)
        assert consumer._errors == 1

    def test_parse_event_from_lab_stream(self, coordinator):
        consumer = EcosystemEventConsumer(redis_client=None, coordinator=coordinator)
        data = {
            "patient_id": "p1",
            "source_module": "intellicare-florence",
            "payload": '{"hba1c": 9.5}',
        }
        event = consumer._parse_event("intellicare:events:lab", data)
        assert isinstance(event, IntelliCareEvent)
        assert event.event_type == "lab_result_critical"
        assert event.patient_id == "p1"
        assert event.payload == {"hba1c": 9.5}

    def test_parse_event_custom_type(self, coordinator):
        consumer = EcosystemEventConsumer(redis_client=None, coordinator=coordinator)
        data = {"event_type": "custom_event", "patient_id": "p2", "source_module": "test"}
        event = consumer._parse_event("intellicare:events:vitals", data)
        assert event.event_type == "custom_event"
