"""Testes de fluxo para o RoutingEngine - Fase 2 (corrigido)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from comunicacao.dispatchers.base import (
    ChannelCapabilities,
    ChannelHealth,
    DeliveryStatus,
    DispatchResult,
    DispatcherManager,
    RecipientValidation,
    ResolvedRecipient,
)
from comunicacao.routing.engine import RoutingEngine
from comunicacao.routing.fallback_monitor import FallbackMonitor, RetryConfig
from comunicacao.routing.lgpd import DefaultLGPDGateway
from comunicacao.routing.models import (
    CommunicationIntentCreate,
    CommunicationIntentRecord,
    IntentStatus,
    RecipientType,
    ChannelStep,
)
from comunicacao.routing.recipient_resolver import RecipientResolver
from comunicacao.routing.rule_matcher import RuleMatcher
from comunicacao.routing.store import InMemoryRoutingStore
from comunicacao.storage.rule_repository import InMemoryRuleStore, RoutingRuleChannel


@pytest.fixture
def routing_store():
    return InMemoryRoutingStore()


@pytest.fixture
def rule_store():
    from comunicacao.routing.models import RoutingRule as _RoutingRule
    store = InMemoryRuleStore()
    rule = _RoutingRule(
        id=str(uuid4()),
        name="Regra Catch-All",
        priority=100,
        severities=[],
        categories=[],
        recipient_types=[],
        channels=[
            ChannelStep(channel="rocketchat", timeout_seconds=30),
            ChannelStep(channel="email", timeout_seconds=60),
        ],
        active=True,
    )
    store.save_rule(rule)
    return store


@pytest.fixture
def recipient_resolver():
    return RecipientResolver()


@pytest.fixture
def lgpd_gateway():
    return DefaultLGPDGateway()


@pytest.fixture
def dispatcher_manager():
    manager = DispatcherManager()

    mock_dispatcher = MagicMock()
    mock_dispatcher.channel = "rocketchat"
    mock_dispatcher.send = AsyncMock(return_value=DispatchResult(
        success=True,
        channel_message_id="rc-msg-123",
    ))
    mock_dispatcher.get_status = AsyncMock(return_value=DeliveryStatus.SENT)
    mock_dispatcher.cancel = AsyncMock(return_value=False)
    mock_dispatcher.health_check = AsyncMock(return_value=ChannelHealth(
        channel="rocketchat", available=True, status="up",
    ))
    mock_dispatcher.test_send = AsyncMock(return_value=DispatchResult(
        success=True, channel_message_id="test-rc-123",
    ))
    mock_dispatcher.get_capabilities = AsyncMock(return_value=ChannelCapabilities(
        channel="rocketchat", supports_read_receipt=True, supports_rich_content=True,
    ))
    mock_dispatcher.validate_recipient = AsyncMock(return_value=RecipientValidation(
        valid=True, recipient_id="prof-123",
    ))
    manager.register(mock_dispatcher)

    mock_email = MagicMock()
    mock_email.channel = "email"
    mock_email.send = AsyncMock(return_value=DispatchResult(
        success=True, channel_message_id="email-msg-123",
    ))
    mock_email.get_status = AsyncMock(return_value=DeliveryStatus.SENT)
    mock_email.cancel = AsyncMock(return_value=False)
    mock_email.health_check = AsyncMock(return_value=ChannelHealth(
        channel="email", available=True, status="up",
    ))
    mock_email.test_send = AsyncMock(return_value=DispatchResult(
        success=True, channel_message_id="test-email-123",
    ))
    mock_email.get_capabilities = AsyncMock(return_value=ChannelCapabilities(
        channel="email", supports_read_receipt=True, supports_rich_content=True,
    ))
    mock_email.validate_recipient = AsyncMock(return_value=RecipientValidation(
        valid=True, recipient_id="prof-123",
    ))
    manager.register(mock_email)
    return manager


@pytest.fixture
def template_store():
    from comunicacao.storage.template_repository import InMemoryTemplateStore
    return InMemoryTemplateStore()


@pytest.fixture
def routing_engine(routing_store, template_store, rule_store, recipient_resolver, lgpd_gateway, dispatcher_manager):
    rule_matcher = RuleMatcher(rule_store=rule_store)
    fast_config = RetryConfig(initial_delay_seconds=0, max_delay_seconds=0)
    fallback_monitor = FallbackMonitor(
        routing_store=routing_store,
        dispatcher_manager=dispatcher_manager,
        default_retry_config=fast_config,
    )
    return RoutingEngine(
        routing_store=routing_store,
        template_store=template_store,
        rule_matcher=rule_matcher,
        recipient_resolver=recipient_resolver,
        lgpd_gateway=lgpd_gateway,
        dispatcher_manager=dispatcher_manager,
        fallback_monitor=fallback_monitor,
    )


# ============================================================================
# TESTES DE FLUXO
# ============================================================================


@pytest.mark.asyncio
async def test_happy_path_intent_to_completed(routing_engine, routing_store):
    intent_data = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-001",
        correlation_id="corr-001",
        recipient_type=RecipientType.PROFESSIONAL,
        recipient_id="prof-123",
        severity="high",
        category="clinical_alert",
        content_raw="Alerta: Paciente com sinais vitais criticos",
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    assert result.status == IntentStatus.COMPLETED
    assert result.id == intent.id

    timeline_events = [event.event_type for event in result.timeline]
    assert "intent_created" in timeline_events
    assert "processing_started" in timeline_events
    assert "recipient_resolved" in timeline_events
    assert "lgpd_checked" in timeline_events
    assert "rules_matched" in timeline_events
    assert "dispatched" in timeline_events
    assert "lgpd_blocked" not in timeline_events
    assert "no_rules_matched" not in timeline_events
    assert "processing_failed" not in timeline_events


@pytest.mark.asyncio
async def test_lgpd_blocked_flow(routing_engine, lgpd_gateway):
    lgpd_gateway.check_compliance = AsyncMock(return_value=False)
    intent_data = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-002",
        correlation_id="corr-002",
        recipient_type=RecipientType.PATIENT,
        recipient_id="patient-456",
        severity="low",
        category="marketing",
        content_raw="Novidades do sistema",
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    assert result.status == IntentStatus.FAILED
    timeline_events = [event.event_type for event in result.timeline]
    assert "lgpd_blocked" in timeline_events
    assert "dispatched" not in timeline_events


@pytest.mark.asyncio
async def test_no_rules_matched_flow(routing_engine, rule_store):
    rule_store._rules.clear()
    intent_data = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-003",
        correlation_id="corr-003",
        recipient_type=RecipientType.PROFESSIONAL,
        recipient_id="prof-789",
        severity="medium",
        category="notification",
        content_raw="Notificacao geral",
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    assert result.status == IntentStatus.FAILED
    timeline_events = [event.event_type for event in result.timeline]
    assert "no_rules_matched" in timeline_events
    assert "dispatched" not in timeline_events


@pytest.mark.asyncio
async def test_dispatch_failure_flow(routing_engine, dispatcher_manager):
    for dispatcher in dispatcher_manager._dispatchers.values():
        dispatcher.send = AsyncMock(return_value=DispatchResult(
            success=False,
            error_code="connection_error",
            error_message="Falha ao conectar ao servidor",
        ))
    intent_data = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-004",
        correlation_id="corr-004",
        recipient_type=RecipientType.PROFESSIONAL,
        recipient_id="prof-999",
        severity="high",
        category="clinical_alert",
        content_raw="Alerta critico",
        max_attempts=1,
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    timeline_events = [event.event_type for event in result.timeline]
    assert "processing_started" in timeline_events


@pytest.mark.asyncio
async def test_timeline_append_only(routing_engine):
    intent_data = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-005",
        correlation_id="corr-005",
        recipient_type=RecipientType.PROFESSIONAL,
        recipient_id="prof-111",
        severity="high",
        category="clinical_alert",
        content_raw="Teste de timeline",
    )
    intent = await routing_engine.create_intent(intent_data)
    assert len(intent.timeline) == 1
    assert intent.timeline[0].event_type == "intent_created"
    initial_timeline_length = len(intent.timeline)

    result = await routing_engine.process_intent(intent.id)

    assert len(result.timeline) > initial_timeline_length
    assert result.timeline[0].event_type == "intent_created"
    for event in result.timeline:
        assert event.timestamp is not None


@pytest.mark.asyncio
async def test_preferred_channel_priority(routing_engine, rule_store):
    intent_data = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-006",
        correlation_id="corr-006",
        recipient_type=RecipientType.PROFESSIONAL,
        recipient_id="prof-222",
        severity="high",
        category="clinical_alert",
        content_raw="Teste de preferred channel",
        preferred_channel="email",
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    assert result.status == IntentStatus.COMPLETED
    timeline_events = [event.event_type for event in result.timeline]
    assert "rules_matched" in timeline_events


@pytest.mark.asyncio
async def test_excluded_channels(routing_engine):
    intent_data = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-007",
        correlation_id="corr-007",
        recipient_type=RecipientType.PROFESSIONAL,
        recipient_id="prof-333",
        severity="high",
        category="clinical_alert",
        content_raw="Teste de excluded channels",
        excluded_channels=["rocketchat"],
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    assert result.status == IntentStatus.COMPLETED


@pytest.mark.asyncio
async def test_idempotency(routing_engine):
    intent_data_1 = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-idempotent",
        correlation_id="corr-idem-1",
        recipient_type=RecipientType.PROFESSIONAL,
        recipient_id="prof-444",
        severity="high",
        category="clinical_alert",
        content_raw="Primeira tentativa",
    )
    intent_data_2 = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-idempotent",
        correlation_id="corr-idem-2",
        recipient_type=RecipientType.PROFESSIONAL,
        recipient_id="prof-555",
        severity="low",
        category="notification",
        content_raw="Segunda tentativa",
    )
    intent_1 = await routing_engine.create_intent(intent_data_1)
    intent_2 = await routing_engine.create_intent(intent_data_2)

    assert intent_1.id == intent_2.id
    assert intent_1.source_event_id == intent_2.source_event_id


@pytest.mark.asyncio
async def test_critical_severity_always_allowed(routing_engine, lgpd_gateway):
    intent_data = CommunicationIntentCreate(
        source_module="florence",
        source_event_id="evt-critical",
        correlation_id="corr-critical",
        recipient_type=RecipientType.PATIENT,
        recipient_id="patient-999",
        severity="critical",
        category="emergency",
        content_raw="Emergencia medica!",
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    timeline_events = [event.event_type for event in result.timeline]
    assert "lgpd_blocked" not in timeline_events
    assert "lgpd_checked" in timeline_events


@pytest.mark.asyncio
async def test_escalation_on_all_channels_failed(routing_engine, routing_store):
    for dispatcher in routing_engine.dispatcher_manager._dispatchers.values():
        dispatcher.send = AsyncMock(return_value=DispatchResult(
            success=False,
            channel_message_id=None,
            error_message="Simulated failure",
        ))
    intent_data = CommunicationIntentCreate(
        correlation_id="test-escalation-001",
        source_module="test",
        source_event_id="evt-escalation",
        recipient_type=RecipientType.PATIENT,
        recipient_id="patient-999",
        severity="high",
        category="clinical_alert",
        content_raw="Alerta clinico importante",
        max_attempts=1,
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    assert result.status == IntentStatus.FAILED

    timeline_events = [event.event_type for event in result.timeline]
    assert "all_channels_failed" in timeline_events
    assert "escalated" in timeline_events

    all_intents = routing_store.list_intents()
    escalation_intents = [
        i for i in all_intents
        if i.category == "escalation" and i.parent_intent_id == result.id
    ]
    assert len(escalation_intents) == 1

    escalation = escalation_intents[0]
    assert escalation.severity == "high"
    assert escalation.recipient_type == RecipientType.COORDINATOR
    assert escalation.parent_intent_id == result.id
    assert "escalation_reason" in escalation.metadata
    assert escalation.metadata["escalation_reason"] == "all_channels_failed"


@pytest.mark.asyncio
async def test_no_escalation_for_low_severity(routing_engine, routing_store):
    for dispatcher in routing_engine.dispatcher_manager._dispatchers.values():
        dispatcher.send = AsyncMock(return_value=DispatchResult(
            success=False,
            channel_message_id=None,
            error_message="Simulated failure",
        ))
    intent_data = CommunicationIntentCreate(
        correlation_id="test-no-escalation-001",
        source_module="test",
        source_event_id="evt-no-escalation",
        recipient_type=RecipientType.PATIENT,
        recipient_id="patient-999",
        severity="medium",
        category="reminder",
        content_raw="Lembrete de medicacao",
        max_attempts=1,
    )
    intent = await routing_engine.create_intent(intent_data)
    result = await routing_engine.process_intent(intent.id)

    assert result.status == IntentStatus.FAILED

    timeline_events = [event.event_type for event in result.timeline]
    assert "all_channels_failed" in timeline_events
    assert "escalated" not in timeline_events

    all_intents = routing_store.list_intents()
    escalation_intents = [
        i for i in all_intents
        if i.category == "escalation"
    ]
    assert len(escalation_intents) == 0
