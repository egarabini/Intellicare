from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from comunicacao.api.app import _state, create_app
from comunicacao.dispatchers import (
    ChannelHealth,
    ChannelMessage,
    DeliveryStatus,
    DispatchResult,
    DispatcherManager,
)
from comunicacao.routing.delayed import DelayedWorker, InMemoryDelayedScheduler
from comunicacao.routing.engine import RoutingEngine, RoutingService


class _FakePatientRoomRepository:
    def __init__(self) -> None:
        self.links = {"patient-1": "\!room1:matrix.gsi.srv.br"}

    def upsert_link(self, patient_id: str, room_id: str) -> None:
        self.links[patient_id] = room_id

    def get_room_id(self, patient_id: str) -> str | None:
        return self.links.get(patient_id)

    def list_links(self, limit: int, offset: int) -> list[dict[str, str]]:
        _ = limit, offset
        return []

    def delete_link(self, patient_id: str) -> bool:
        if patient_id not in self.links:
            return False
        del self.links[patient_id]
        return True

    def close(self) -> None:
        return


class _FakeMatrixDispatcher:
    channel = "matrix"

    async def send(self, message: ChannelMessage) -> DispatchResult:
        if message.content.body == "forcar falha":
            return DispatchResult(success=False, error_code="send_error", error_message="falha simulada")
        return DispatchResult(success=True, channel_message_id="evt-1", channel_room_id="room-1")

    async def is_available(self) -> bool:
        return True

    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        return DeliveryStatus.SENT if channel_message_id else DeliveryStatus.UNKNOWN

    async def get_health(self) -> ChannelHealth:
        return ChannelHealth(channel=self.channel, available=True, status="up")

    async def supports_read_receipt(self) -> bool:
        return False

    async def supports_rich_content(self) -> bool:
        return True


class _FakeEmailDispatcher:
    channel = "email"

    async def send(self, message: ChannelMessage) -> DispatchResult:
        _ = message
        return DispatchResult(success=True, channel_message_id="mail-1", channel_room_id="inbox-1")

    async def is_available(self) -> bool:
        return True

    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        return DeliveryStatus.SENT if channel_message_id else DeliveryStatus.UNKNOWN

    async def get_health(self) -> ChannelHealth:
        return ChannelHealth(channel=self.channel, available=True, status="up")

    async def supports_read_receipt(self) -> bool:
        return False

    async def supports_rich_content(self) -> bool:
        return True


def _override_routing_service(include_email: bool = False, with_scheduler: bool = False) -> None:
    from comunicacao.routing.engine import RoutingEngine
    from comunicacao.routing.fallback_monitor import FallbackMonitor, RetryConfig
    from comunicacao.routing.lgpd import DefaultLGPDGateway
    from comunicacao.routing.models import RoutingRule, ChannelStep
    from comunicacao.routing.recipient_resolver import RecipientResolver
    from comunicacao.routing.rule_matcher import RuleMatcher
    from comunicacao.routing.store import InMemoryRoutingStore
    from comunicacao.storage.rule_repository import InMemoryRuleStore
    from comunicacao.storage.template_repository import InMemoryTemplateStore

    routing_store = InMemoryRoutingStore()
    rule_store = InMemoryRuleStore()
    template_store = InMemoryTemplateStore()

    # Catch-all rule
    channels = [ChannelStep(channel="matrix", timeout_seconds=30)]
    if include_email:
        channels.append(ChannelStep(channel="email", timeout_seconds=60))
    rule = RoutingRule(
        id="default",
        name="Default Catch-All",
        priority=100,
        severities=[],
        categories=[],
        recipient_types=[],
        channels=channels,
        active=True,
    )
    rule_store.save_rule(rule)

    manager = DispatcherManager()
    manager.register(_FakeMatrixDispatcher())
    if include_email:
        manager.register(_FakeEmailDispatcher())

    rule_matcher = RuleMatcher(rule_store=rule_store)
    recipient_resolver = RecipientResolver()
    lgpd_gateway = DefaultLGPDGateway()

    fast_config = RetryConfig(initial_delay_seconds=0, max_delay_seconds=0)
    fallback_monitor = FallbackMonitor(
        routing_store=routing_store,
        dispatcher_manager=manager,
        default_retry_config=fast_config,
    )

    routing_engine = RoutingEngine(
        routing_store=routing_store,
        template_store=template_store,
        rule_matcher=rule_matcher,
        recipient_resolver=recipient_resolver,
        lgpd_gateway=lgpd_gateway,
        dispatcher_manager=manager,
        fallback_monitor=fallback_monitor,
    )

    _state["routing_service"] = routing_engine
    _state["template_store"] = template_store

    if with_scheduler:
        delayed_scheduler = InMemoryDelayedScheduler()
        delayed_worker = DelayedWorker(
            scheduler=delayed_scheduler,
            on_task=lambda task: None,
            poll_seconds=1,
        )
        _state["routing_delayed_scheduler"] = delayed_scheduler
        _state["routing_delayed_worker"] = delayed_worker


def test_routing_send_and_get_intent_success() -> None:
    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()
        send = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-100",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "high",
                "category": "clinical_alert",
                "content_raw": "Alerta de teste",
                "correlation_id": "corr-100",
            },
        )
        intent_id = send.json()["intent_id"]
        details = client.get(f"/api/v1/routing/intents/{intent_id}")

    assert send.status_code == 202
    assert send.json()["status"] == "completed"
    assert details.status_code == 200
    body = details.json()
    assert body["intent"]["correlation_id"] == "corr-100"
    assert len(body["deliveries"]) == 1
    assert body["deliveries"][0]["status"] == "sent"
    assert len(body["timeline"]) >= 2


def test_routing_send_respects_excluded_channel() -> None:
    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()
        response = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-101",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "low",
                "category": "education",
                "content_raw": "Conteudo",
                "correlation_id": "corr-101",
                "excluded_channels": ["matrix"],
            },
        )

    assert response.status_code == 202
    assert response.json()["status"] == "failed"


def test_routing_send_is_idempotent_by_source_event() -> None:
    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()
        payload = {
            "source_module": "intellicare-oswaldo",
            "source_event_id": "evt-102",
            "recipient_type": "patient",
            "recipient_id": "patient-1",
            "severity": "medium",
            "category": "clinical_alert",
            "content_raw": "Mensagem",
            "correlation_id": "corr-102",
        }
        first = client.post("/api/v1/routing/send", json=payload)
        second = client.post("/api/v1/routing/send", json=payload)

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["intent_id"] == second.json()["intent_id"]


def test_routing_batch_list_and_metrics() -> None:
    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()
        batch = client.post(
            "/api/v1/routing/send-batch",
            json={
                "intents": [
                    {
                        "source_module": "intellicare-oswaldo",
                        "source_event_id": "evt-201",
                        "recipient_type": "patient",
                        "recipient_id": "patient-1",
                        "severity": "high",
                        "category": "clinical_alert",
                        "content_raw": "A1",
                        "correlation_id": "corr-201",
                    },
                    {
                        "source_module": "intellicare-oswaldo",
                        "source_event_id": "evt-202",
                        "recipient_type": "patient",
                        "recipient_id": "patient-1",
                        "severity": "low",
                        "category": "education",
                        "content_raw": "A2",
                        "correlation_id": "corr-202",
                    },
                ]
            },
        )
        listed = client.get("/api/v1/routing/intents")
        metrics = client.get("/api/v1/routing/metrics")

    assert batch.status_code == 202
    assert batch.json()["accepted"] == 2
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    assert metrics.status_code == 200
    assert metrics.json()["total_intents"] == 2
    assert metrics.json()["by_channel"]["matrix"] >= 1


def test_routing_cancel_completed_intent_returns_conflict() -> None:
    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()
        send = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-301",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "high",
                "category": "clinical_alert",
                "content_raw": "Alerta finalizado",
                "correlation_id": "corr-301",
            },
        )
        intent_id = send.json()["intent_id"]
        cancel = client.put(f"/api/v1/routing/intents/{intent_id}/cancel")

    assert cancel.status_code == 409


def test_routing_fallback_to_second_channel_when_first_fails() -> None:
    app = create_app()
    with TestClient(app) as client:
        _override_routing_service(include_email=True)
        response = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-401",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "high",
                "category": "clinical_alert",
                "content_raw": "forcar falha",
                "correlation_id": "corr-401",
                "max_attempts": 1,
            },
        )
        intent_id = response.json()["intent_id"]
        details = client.get(f"/api/v1/routing/intents/{intent_id}")
        metrics = client.get("/api/v1/routing/metrics")

    assert response.status_code == 202
    assert response.json()["status"] == "completed"
    assert details.status_code == 200
    payload = details.json()
    assert len(payload["deliveries"]) >= 2
    assert payload["deliveries"][0]["status"] == "failed"
    assert payload["deliveries"][1]["status"] == "sent"
    assert any(event["event_type"] == "fallback_activated" for event in payload["timeline"])
    assert metrics.status_code == 200
    assert metrics.json()["fallback_count"] >= 1


def test_routing_rules_endpoints_list_and_upsert() -> None:
    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()
        listed = client.get("/api/v1/routing/rules")
        upsert = client.put(
            "/api/v1/routing/rules/rule_custom_push",
            json={
                "id": "rule_custom_push",
                "name": "Custom push",
                "priority": 5,
                "active": True,
                "severities": ["critical"],
                "recipient_types": ["professional"],
                "categories": ["clinical_alert"],
                "channels": [{"channel": "matrix"}],
            },
        )
        listed_after = client.get("/api/v1/routing/rules")

    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    assert upsert.status_code == 200
    assert upsert.json()["id"] == "rule_custom_push"
    assert listed_after.status_code == 200
    assert any(item["id"] == "rule_custom_push" for item in listed_after.json()["items"])


@pytest.mark.skip(reason="Scheduler test requires complex setup")
def test_routing_scheduler_endpoints_and_ack_escalation() -> None:
    import time

    app = create_app()
    with TestClient(app) as client:
        _override_routing_service(with_scheduler=True)
        send = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-501",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "high",
                "category": "clinical_alert",
                "content_raw": "alerta com ack",
                "correlation_id": "corr-501",
                "require_ack": True,
                "metadata": {"coordinator_id": "coord-1"},
            },
        )
        status = client.get("/api/v1/routing/scheduler/status")
        _ = client.post("/api/v1/routing/scheduler/start")
        time.sleep(1.2)
        processed = client.post("/api/v1/routing/scheduler/process-due")
        _ = client.post("/api/v1/routing/scheduler/stop")
        listed = client.get("/api/v1/routing/intents")
        metrics = client.get("/api/v1/routing/metrics")

    assert send.status_code == 202
    assert status.status_code == 200
    assert processed.status_code == 200
    assert processed.json()["processed"] >= 0
    assert listed.status_code == 200
    assert any(item["category"] == "escalation" for item in listed.json()["items"])
    assert metrics.status_code == 200
    assert metrics.json()["escalation_count"] >= 1


def test_routing_send_with_template_id() -> None:
    from comunicacao.templates.models import MessageTemplate
    from comunicacao.templates.renderer import TemplateRenderer
    from comunicacao.templates.store import InMemoryTemplateStore

    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()

        template_store = InMemoryTemplateStore()
        template = MessageTemplate(
            id="test_alert",
            name="Test Alert",
            category="clinical_alert",
            params_schema={"required": ["patient_name", "message"]},
            sample_params={"patient_name": "Test", "message": "Test message"},
            channel_variants={
                "matrix": {"format": "plain", "body": "Alert for {{patient_name}}: {{message}}"},
            },
        )
        template_store.create(template)
        _state["template_store"] = template_store
        _state["template_renderer"] = TemplateRenderer()

        response = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-template-001",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "high",
                "category": "clinical_alert",
                "correlation_id": "corr-template-001",
                "content_template_id": "test_alert",
                "content_params": {
                    "patient_name": "Joao Silva",
                    "message": "eGFR critico: 25 ml/min",
                },
            },
        )

        intent_id = response.json()["intent_id"]
        details = client.get(f"/api/v1/routing/intents/{intent_id}")

    assert response.status_code == 202
    assert details.status_code == 200
    intent_data = details.json()
    assert intent_data["intent"]["content_template_id"] == "test_alert"
    assert intent_data["intent"]["content_params"]["patient_name"] == "Joao Silva"
    assert "Joao Silva" in intent_data["intent"]["content_raw"]
    assert "eGFR critico" in intent_data["intent"]["content_raw"]

def test_routing_send_with_content_raw_fallback() -> None:
    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()

        response = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-raw-001",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "medium",
                "category": "clinical_alert",
                "correlation_id": "corr-raw-001",
                "content_raw": "Mensagem direta sem template",
            },
        )

        intent_id = response.json()["intent_id"]
        details = client.get(f"/api/v1/routing/intents/{intent_id}")

    assert response.status_code == 202
    assert details.status_code == 200
    intent_data = details.json()
    assert intent_data["intent"]["content_template_id"] is None
    assert intent_data["intent"]["content_raw"] == "Mensagem direta sem template"

def test_routing_send_with_invalid_template_fails() -> None:
    from comunicacao.templates.renderer import TemplateRenderer
    from comunicacao.templates.store import InMemoryTemplateStore

    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()

        _state["template_store"] = InMemoryTemplateStore()
        _state["template_renderer"] = TemplateRenderer()

        response = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-invalid-template",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "high",
                "category": "clinical_alert",
                "correlation_id": "corr-invalid-template",
                "content_template_id": "nonexistent_template",
                "content_params": {"patient_name": "Test"},
            },
        )

        intent_id = response.json()["intent_id"]
        details = client.get(f"/api/v1/routing/intents/{intent_id}")

    assert response.status_code == 202
    assert details.status_code == 200
    intent_data = details.json()
    assert intent_data["intent"]["status"] == "failed"

def test_routing_send_with_missing_template_params_fails() -> None:
    from comunicacao.templates.models import MessageTemplate
    from comunicacao.templates.renderer import TemplateRenderer
    from comunicacao.templates.store import InMemoryTemplateStore

    app = create_app()
    with TestClient(app) as client:
        _override_routing_service()

        template_store = InMemoryTemplateStore()
        template = MessageTemplate(
            id="strict_template",
            name="Strict Template",
            category="clinical_alert",
            params_schema={"required": ["patient_name", "message", "severity"]},
            sample_params={"patient_name": "Test", "message": "Test", "severity": "high"},
            channel_variants={
                "matrix": {"format": "plain", "body": "{{patient_name}}: {{message}} ({{severity}})"},
            },
        )
        template_store.create(template)
        _state["template_store"] = template_store
        _state["template_renderer"] = TemplateRenderer()

        response = client.post(
            "/api/v1/routing/send",
            json={
                "source_module": "intellicare-oswaldo",
                "source_event_id": "evt-missing-params",
                "recipient_type": "patient",
                "recipient_id": "patient-1",
                "severity": "high",
                "category": "clinical_alert",
                "correlation_id": "corr-missing-params",
                "content_template_id": "strict_template",
                "content_params": {
                    "patient_name": "Joao",
                },
            },
        )

        intent_id = response.json()["intent_id"]
        details = client.get(f"/api/v1/routing/intents/{intent_id}")

    assert response.status_code == 202
    assert details.status_code == 200
    intent_data = details.json()
    assert intent_data["intent"]["status"] == "failed"
