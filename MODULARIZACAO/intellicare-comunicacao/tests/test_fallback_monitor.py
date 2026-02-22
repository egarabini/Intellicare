"""Testes para FallbackMonitor - Fase 3."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from comunicacao.dispatchers.base import DispatchResult
from comunicacao.routing.fallback_monitor import (
    ChannelAttempt,
    FallbackMonitor,
    RetryConfig,
)
from comunicacao.routing.models import (
    CommunicationIntentRecord,
    IntentStatus,
    RecipientType,
)
from comunicacao.storage.routing_repository import InMemoryRoutingStore


@pytest.fixture
def routing_store():
    """Fixture para routing store."""
    return InMemoryRoutingStore()


@pytest.fixture
def dispatcher_manager():
    """Fixture para dispatcher manager."""
    from comunicacao.dispatchers.base import DispatcherManager
    
    manager = DispatcherManager()
    
    # Registra dispatchers mock
    for channel in ["rocketchat", "email", "sms"]:
        dispatcher = MagicMock()
        dispatcher.send = AsyncMock(return_value=DispatchResult(success=True))
        manager._dispatchers[channel] = dispatcher
    
    return manager


@pytest.fixture
def fallback_monitor(routing_store, dispatcher_manager):
    """Fixture para fallback monitor."""
    return FallbackMonitor(
        routing_store=routing_store,
        dispatcher_manager=dispatcher_manager,
    )


@pytest.fixture
def sample_intent():
    """Fixture para intent de teste."""
    return CommunicationIntentRecord(
        id=uuid4(),
        source_module="test",
        source_event_id="evt-001",
        recipient_type=RecipientType.PATIENT,
        recipient_id="patient-123",
        severity="high",
        category="clinical_alert",
        content_raw="Alerta clínico importante",
        correlation_id="test-001",
        status=IntentStatus.PENDING,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        max_attempts=3,
        timeline=[],
    )


# ============================================================================
# TESTES DE RETRY DELAY (EXPONENTIAL BACKOFF)
# ============================================================================

def test_calculate_retry_delay_exponential(fallback_monitor):
    """Testa cálculo de delay com exponential backoff."""
    config = RetryConfig(
        initial_delay_seconds=5,
        exponential_base=2.0,
        max_delay_seconds=300,
    )
    
    # Tentativa 1: 5 * (2^0) = 5
    assert fallback_monitor.calculate_retry_delay(1, config) == 5
    
    # Tentativa 2: 5 * (2^1) = 10
    assert fallback_monitor.calculate_retry_delay(2, config) == 10
    
    # Tentativa 3: 5 * (2^2) = 20
    assert fallback_monitor.calculate_retry_delay(3, config) == 20
    
    # Tentativa 4: 5 * (2^3) = 40
    assert fallback_monitor.calculate_retry_delay(4, config) == 40


def test_calculate_retry_delay_max_cap(fallback_monitor):
    """Testa que delay não excede max_delay_seconds."""
    config = RetryConfig(
        initial_delay_seconds=100,
        exponential_base=2.0,
        max_delay_seconds=150,
    )
    
    # Tentativa 10: 100 * (2^9) = 51200, mas limitado a 150
    delay = fallback_monitor.calculate_retry_delay(10, config)
    assert delay == 150


# ============================================================================
# TESTES DE EXPIRAÇÃO
# ============================================================================

def test_is_expired_no_expiry(fallback_monitor, sample_intent):
    """Testa que intent sem expires_at nunca expira."""
    sample_intent.expires_at = None
    assert fallback_monitor.is_expired(sample_intent) is False


def test_is_expired_future(fallback_monitor, sample_intent):
    """Testa que intent com expires_at futuro não expirou."""
    sample_intent.expires_at = datetime.now(UTC) + timedelta(hours=1)
    assert fallback_monitor.is_expired(sample_intent) is False


def test_is_expired_past(fallback_monitor, sample_intent):
    """Testa que intent com expires_at passado expirou."""
    sample_intent.expires_at = datetime.now(UTC) - timedelta(minutes=5)
    assert fallback_monitor.is_expired(sample_intent) is True


# ============================================================================
# TESTES DE SHOULD_RETRY
# ============================================================================

def test_should_retry_within_max_attempts(fallback_monitor, sample_intent):
    """Testa que should_retry retorna True dentro de max_attempts."""
    sample_intent.max_attempts = 3
    assert fallback_monitor.should_retry(sample_intent, "rocketchat", 1) is True
    assert fallback_monitor.should_retry(sample_intent, "rocketchat", 2) is True


def test_should_retry_exceeds_max_attempts(fallback_monitor, sample_intent):
    """Testa que should_retry retorna False quando excede max_attempts."""
    sample_intent.max_attempts = 3
    assert fallback_monitor.should_retry(sample_intent, "rocketchat", 3) is False
    assert fallback_monitor.should_retry(sample_intent, "rocketchat", 4) is False


def test_should_retry_expired_intent(fallback_monitor, sample_intent):
    """Testa que should_retry retorna False para intent expirado."""
    sample_intent.max_attempts = 3
    sample_intent.expires_at = datetime.now(UTC) - timedelta(minutes=5)
    assert fallback_monitor.should_retry(sample_intent, "rocketchat", 1) is False


# ============================================================================
# TESTES DE TRY_CHANNEL
# ============================================================================

@pytest.mark.asyncio
async def test_try_channel_success(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa envio bem-sucedido em um canal."""
    # Configura dispatcher para sucesso
    dispatcher_manager._dispatchers["rocketchat"].send = AsyncMock(
        return_value=DispatchResult(success=True)
    )

    attempt = await fallback_monitor.try_channel(
        intent=sample_intent,
        channel="rocketchat",
        attempt_number=1,
    )

    assert attempt.channel == "rocketchat"
    assert attempt.attempt_number == 1
    assert attempt.completed is True
    assert attempt.success is True
    assert attempt.error_message is None


@pytest.mark.asyncio
async def test_try_channel_failure(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa envio com falha em um canal."""
    # Configura dispatcher para falha
    dispatcher_manager._dispatchers["rocketchat"].send = AsyncMock(
        return_value=DispatchResult(success=False, error_message="Connection failed")
    )

    attempt = await fallback_monitor.try_channel(
        intent=sample_intent,
        channel="rocketchat",
        attempt_number=1,
    )

    assert attempt.completed is True
    assert attempt.success is False
    assert attempt.error_message == "Connection failed"


@pytest.mark.asyncio
async def test_try_channel_timeout(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa timeout em envio de canal."""
    # Configura dispatcher para demorar mais que o timeout
    async def slow_send(message):
        await asyncio.sleep(5)  # Demora 5 segundos
        return DispatchResult(success=True)

    dispatcher_manager._dispatchers["rocketchat"].send = slow_send

    config = RetryConfig(timeout_seconds=1)  # Timeout de 1 segundo

    attempt = await fallback_monitor.try_channel(
        intent=sample_intent,
        channel="rocketchat",
        attempt_number=1,
        config=config,
    )

    assert attempt.completed is True
    assert attempt.success is False
    assert "Timeout" in attempt.error_message


@pytest.mark.asyncio
async def test_try_channel_dispatcher_not_found(fallback_monitor, sample_intent):
    """Testa erro quando dispatcher não existe."""
    attempt = await fallback_monitor.try_channel(
        intent=sample_intent,
        channel="nonexistent",
        attempt_number=1,
    )

    assert attempt.completed is True
    assert attempt.success is False
    assert "não encontrado" in attempt.error_message


# ============================================================================
# TESTES DE TRY_WITH_RETRY
# ============================================================================

@pytest.mark.asyncio
async def test_try_with_retry_success_first_attempt(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa retry com sucesso na primeira tentativa."""
    dispatcher_manager._dispatchers["rocketchat"].send = AsyncMock(
        return_value=DispatchResult(success=True)
    )

    success = await fallback_monitor.try_with_retry(
        intent=sample_intent,
        channel="rocketchat",
    )

    assert success is True

    # Verifica que apenas 1 tentativa foi registrada
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 1
    assert attempts[0].success is True


@pytest.mark.asyncio
async def test_try_with_retry_success_after_failures(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa retry com sucesso após falhas."""
    # Configura dispatcher para falhar 2 vezes e depois suceder
    call_count = 0

    async def send_with_retries(message):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return DispatchResult(success=False, error_message="Temporary failure")
        return DispatchResult(success=True)

    dispatcher_manager._dispatchers["rocketchat"].send = send_with_retries

    config = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=0,  # Sem delay para teste rápido
    )

    success = await fallback_monitor.try_with_retry(
        intent=sample_intent,
        channel="rocketchat",
        config=config,
    )

    assert success is True

    # Verifica que 3 tentativas foram registradas
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 3
    assert attempts[0].success is False
    assert attempts[1].success is False
    assert attempts[2].success is True


@pytest.mark.asyncio
async def test_try_with_retry_all_failures(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa retry com todas as tentativas falhando."""
    dispatcher_manager._dispatchers["rocketchat"].send = AsyncMock(
        return_value=DispatchResult(success=False, error_message="Permanent failure")
    )

    sample_intent.max_attempts = 3

    config = RetryConfig(
        initial_delay_seconds=0,  # Sem delay para teste rápido
    )

    success = await fallback_monitor.try_with_retry(
        intent=sample_intent,
        channel="rocketchat",
        config=config,
    )

    assert success is False

    # Verifica que 3 tentativas foram registradas
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 3
    assert all(not attempt.success for attempt in attempts)


@pytest.mark.asyncio
async def test_try_with_retry_expired_intent(fallback_monitor, sample_intent):
    """Testa que retry para quando intent expira."""
    sample_intent.expires_at = datetime.now(UTC) - timedelta(minutes=5)

    success = await fallback_monitor.try_with_retry(
        intent=sample_intent,
        channel="rocketchat",
    )

    assert success is False

    # Verifica que nenhuma tentativa foi registrada
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 0


# ============================================================================
# TESTES DE TRY_CHANNEL_SEQUENCE (FALLBACK)
# ============================================================================

@pytest.mark.asyncio
async def test_try_channel_sequence_success_first_channel(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa fallback com sucesso no primeiro canal."""
    dispatcher_manager._dispatchers["rocketchat"].send = AsyncMock(
        return_value=DispatchResult(success=True)
    )

    success, channel_used = await fallback_monitor.try_channel_sequence(
        intent=sample_intent,
        channels=["rocketchat", "email", "sms"],
    )

    assert success is True
    assert channel_used == "rocketchat"

    # Verifica que apenas rocketchat foi tentado
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 1
    assert attempts[0].channel == "rocketchat"


@pytest.mark.asyncio
async def test_try_channel_sequence_fallback_to_second(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa fallback para segundo canal após falha no primeiro."""
    # Rocketchat falha, email sucede
    dispatcher_manager._dispatchers["rocketchat"].send = AsyncMock(
        return_value=DispatchResult(success=False, error_message="Rocketchat down")
    )
    dispatcher_manager._dispatchers["email"].send = AsyncMock(
        return_value=DispatchResult(success=True)
    )

    sample_intent.max_attempts = 2

    config = RetryConfig(
        initial_delay_seconds=0,  # Sem delay para teste rápido
    )

    success, channel_used = await fallback_monitor.try_channel_sequence(
        intent=sample_intent,
        channels=["rocketchat", "email", "sms"],
        config=config,
    )

    assert success is True
    assert channel_used == "email"

    # Verifica tentativas: 2 no rocketchat (max_attempts=2), 1 no email
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 3
    assert attempts[0].channel == "rocketchat"
    assert attempts[1].channel == "rocketchat"
    assert attempts[2].channel == "email"


@pytest.mark.asyncio
async def test_try_channel_sequence_all_channels_fail(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa fallback quando todos os canais falham."""
    # Todos os dispatchers falham
    for channel in ["rocketchat", "email", "sms"]:
        dispatcher_manager._dispatchers[channel].send = AsyncMock(
            return_value=DispatchResult(success=False, error_message=f"{channel} failed")
        )

    sample_intent.max_attempts = 2

    config = RetryConfig(
        initial_delay_seconds=0,  # Sem delay para teste rápido
    )

    success, channel_used = await fallback_monitor.try_channel_sequence(
        intent=sample_intent,
        channels=["rocketchat", "email", "sms"],
        config=config,
    )

    assert success is False
    assert channel_used is None

    # Verifica tentativas: 2 por canal = 6 total
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 6


@pytest.mark.asyncio
async def test_try_channel_sequence_expired_during_sequence(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa que sequence para quando intent expira durante execução."""
    # Primeiro canal falha
    dispatcher_manager._dispatchers["rocketchat"].send = AsyncMock(
        return_value=DispatchResult(success=False)
    )

    # Intent expira em 1 segundo
    sample_intent.expires_at = datetime.now(UTC) + timedelta(seconds=1)
    sample_intent.max_attempts = 1

    # Aguarda expiração
    await asyncio.sleep(1.1)

    success, channel_used = await fallback_monitor.try_channel_sequence(
        intent=sample_intent,
        channels=["rocketchat", "email", "sms"],
    )

    assert success is False
    assert channel_used is None


# ============================================================================
# TESTES DE ESCALATION
# ============================================================================

@pytest.mark.asyncio
async def test_escalate_creates_new_intent(fallback_monitor, sample_intent, routing_store):
    """Testa que escalate cria nova intent."""
    # Registra algumas tentativas falhadas
    fallback_monitor._active_attempts[sample_intent.id] = [
        ChannelAttempt(
            channel="rocketchat",
            attempt_number=1,
            started_at=datetime.now(UTC),
            timeout_at=datetime.now(UTC) + timedelta(seconds=30),
            completed=True,
            success=False,
            error_message="Failed",
        ),
        ChannelAttempt(
            channel="email",
            attempt_number=1,
            started_at=datetime.now(UTC),
            timeout_at=datetime.now(UTC) + timedelta(seconds=30),
            completed=True,
            success=False,
            error_message="Failed",
        ),
    ]

    escalation_id = await fallback_monitor.escalate(
        intent=sample_intent,
        reason="all_channels_failed",
    )

    assert escalation_id is not None

    # Busca escalation no store
    escalation = routing_store.get_intent(str(escalation_id))

    assert escalation is not None
    assert escalation.parent_intent_id == sample_intent.id
    assert escalation.category == "escalation"
    assert escalation.recipient_type == RecipientType.COORDINATOR
    assert escalation.severity == "high"  # Mantém HIGH

    # Verifica metadata
    assert escalation.metadata["escalation_reason"] == "all_channels_failed"
    assert escalation.metadata["original_intent_id"] == str(sample_intent.id)
    assert set(escalation.metadata["failed_channels"]) == {"rocketchat", "email"}
    assert escalation.metadata["total_attempts"] == 2


@pytest.mark.asyncio
async def test_escalate_maintains_critical_severity(fallback_monitor, routing_store):
    """Testa que escalate mantém severity CRITICAL."""
    intent = CommunicationIntentRecord(
        id=uuid4(),
        source_module="test",
        source_event_id="evt-critical",
        recipient_type=RecipientType.PATIENT,
        recipient_id="patient-123",
        severity="critical",  # CRITICAL
        category="clinical_alert",
        content_raw="Alerta crítico",
        correlation_id="test-critical",
        status=IntentStatus.PENDING,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        max_attempts=3,
        timeline=[],
    )

    escalation_id = await fallback_monitor.escalate(
        intent=intent,
        reason="all_channels_failed",
    )

    escalation = routing_store.get_intent(str(escalation_id))
    assert escalation.severity == "critical"  # Mantém CRITICAL


@pytest.mark.asyncio
async def test_escalate_elevates_medium_to_high(fallback_monitor, routing_store):
    """Testa que escalate eleva MEDIUM para HIGH."""
    intent = CommunicationIntentRecord(
        id=uuid4(),
        source_module="test",
        source_event_id="evt-medium",
        recipient_type=RecipientType.PATIENT,
        recipient_id="patient-123",
        severity="medium",  # MEDIUM
        category="reminder",
        content_raw="Lembrete",
        correlation_id="test-medium",
        status=IntentStatus.PENDING,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        max_attempts=3,
        timeline=[],
    )

    escalation_id = await fallback_monitor.escalate(
        intent=intent,
        reason="all_channels_failed",
    )

    escalation = routing_store.get_intent(str(escalation_id))
    assert escalation.severity == "high"  # Eleva para HIGH


@pytest.mark.asyncio
async def test_escalate_content_format(fallback_monitor, sample_intent):
    """Testa formato do conteúdo de escalation."""
    fallback_monitor._active_attempts[sample_intent.id] = [
        ChannelAttempt(
            channel="rocketchat",
            attempt_number=1,
            started_at=datetime.now(UTC),
            timeout_at=datetime.now(UTC) + timedelta(seconds=30),
            completed=True,
            success=False,
            error_message="Failed",
        ),
    ]

    escalation_id = await fallback_monitor.escalate(
        intent=sample_intent,
        reason="all_channels_failed",
    )

    from comunicacao.storage.routing_repository import InMemoryRoutingStore
    store = fallback_monitor.routing_store
    escalation = store.get_intent(str(escalation_id))

    content = escalation.content_raw

    # Verifica elementos do conteúdo
    assert "ESCALATION ALERT" in content
    assert "all_channels_failed" in content
    assert str(sample_intent.id) in content
    assert "rocketchat" in content
    assert sample_intent.content_raw in content


# ============================================================================
# TESTES DE GET_ATTEMPTS E CLEAR_ATTEMPTS
# ============================================================================

def test_get_attempts_empty(fallback_monitor, sample_intent):
    """Testa get_attempts quando não há tentativas."""
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert attempts == []


def test_get_attempts_with_data(fallback_monitor, sample_intent):
    """Testa get_attempts com tentativas registradas."""
    # Registra tentativas
    attempt1 = ChannelAttempt(
        channel="rocketchat",
        attempt_number=1,
        started_at=datetime.now(UTC),
        timeout_at=datetime.now(UTC) + timedelta(seconds=30),
        completed=True,
        success=False,
    )
    attempt2 = ChannelAttempt(
        channel="email",
        attempt_number=1,
        started_at=datetime.now(UTC),
        timeout_at=datetime.now(UTC) + timedelta(seconds=30),
        completed=True,
        success=True,
    )

    fallback_monitor._active_attempts[sample_intent.id] = [attempt1, attempt2]

    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 2
    assert attempts[0].channel == "rocketchat"
    assert attempts[1].channel == "email"


def test_clear_attempts(fallback_monitor, sample_intent):
    """Testa clear_attempts."""
    # Registra tentativas
    fallback_monitor._active_attempts[sample_intent.id] = [
        ChannelAttempt(
            channel="rocketchat",
            attempt_number=1,
            started_at=datetime.now(UTC),
            timeout_at=datetime.now(UTC) + timedelta(seconds=30),
        ),
    ]

    # Limpa
    fallback_monitor.clear_attempts(sample_intent.id)

    # Verifica que foi limpo
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert attempts == []


# ============================================================================
# TESTES INTEGRADOS
# ============================================================================

@pytest.mark.asyncio
async def test_full_retry_flow_with_exponential_backoff(fallback_monitor, sample_intent, dispatcher_manager):
    """Testa fluxo completo de retry com exponential backoff."""
    call_times = []

    async def track_send(message):
        call_times.append(datetime.now(UTC))
        return DispatchResult(success=False, error_message="Fail")

    dispatcher_manager._dispatchers["rocketchat"].send = track_send

    sample_intent.max_attempts = 3

    config = RetryConfig(
        initial_delay_seconds=1,
        exponential_base=2.0,
    )

    success = await fallback_monitor.try_with_retry(
        intent=sample_intent,
        channel="rocketchat",
        config=config,
    )

    assert success is False
    assert len(call_times) == 3

    # Verifica delays aproximados
    # Delay 1->2: ~1s
    # Delay 2->3: ~2s
    delay1 = (call_times[1] - call_times[0]).total_seconds()
    delay2 = (call_times[2] - call_times[1]).total_seconds()

    assert 0.9 <= delay1 <= 1.5  # ~1s com margem
    assert 1.9 <= delay2 <= 2.5  # ~2s com margem


@pytest.mark.asyncio
async def test_full_fallback_flow_with_escalation(fallback_monitor, sample_intent, dispatcher_manager, routing_store):
    """Testa fluxo completo: fallback entre canais + escalation."""
    # Todos os canais falham
    for channel in ["rocketchat", "email", "sms"]:
        dispatcher_manager._dispatchers[channel].send = AsyncMock(
            return_value=DispatchResult(success=False, error_message=f"{channel} failed")
        )

    sample_intent.max_attempts = 2
    sample_intent.severity = "high"  # HIGH deve escalar

    config = RetryConfig(
        initial_delay_seconds=0,  # Sem delay para teste rápido
    )

    # Tenta sequência de canais
    success, channel_used = await fallback_monitor.try_channel_sequence(
        intent=sample_intent,
        channels=["rocketchat", "email", "sms"],
        config=config,
    )

    assert success is False
    assert channel_used is None

    # Escala
    escalation_id = await fallback_monitor.escalate(
        intent=sample_intent,
        reason="all_channels_failed",
    )

    assert escalation_id is not None

    # Verifica escalation
    escalation = routing_store.get_intent(str(escalation_id))
    assert escalation.parent_intent_id == sample_intent.id
    assert escalation.category == "escalation"

    # Verifica tentativas registradas: 2 por canal = 6 total
    attempts = fallback_monitor.get_attempts(sample_intent.id)
    assert len(attempts) == 6

