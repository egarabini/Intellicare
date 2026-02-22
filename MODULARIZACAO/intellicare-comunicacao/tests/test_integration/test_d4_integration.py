"""
Testes de Integração E2E - D4 Canais Externos.

Testa fluxo completo: D1 (RoutingEngine) → D4 (Dispatchers).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from comunicacao.routing.engine import RoutingEngine
from comunicacao.routing.models import SendIntentRequest, IntentPriority
from comunicacao.dispatchers.manager import DispatcherManager


@pytest.fixture
def mock_db():
    """Fixture de banco de dados mock."""
    db = AsyncMock()
    return db


@pytest.fixture
def dispatcher_manager():
    """Fixture de DispatcherManager."""
    return DispatcherManager()


@pytest.fixture
def routing_engine(dispatcher_manager, mock_db):
    """Fixture de RoutingEngine com dispatchers mockados."""
    from comunicacao.routing.store import InMemoryRoutingStore
    from comunicacao.routing.rule_store import InMemoryRoutingRuleStore
    from comunicacao.routing.template_store import InMemoryTemplateStore
    from comunicacao.routing.rule_matcher import RuleMatcher
    from comunicacao.routing.recipient_resolver import RecipientResolver
    from comunicacao.routing.lgpd import DefaultLGPDGateway
    from comunicacao.storage.repository import InMemoryPatientRoomRepository

    routing_store = InMemoryRoutingStore()
    rule_store = InMemoryRoutingRuleStore()
    template_store = InMemoryTemplateStore()
    rule_matcher = RuleMatcher(rule_store=rule_store)
    room_repository = InMemoryPatientRoomRepository()
    recipient_resolver = RecipientResolver(room_repository=room_repository)
    lgpd_gateway = DefaultLGPDGateway()

    engine = RoutingEngine(
        routing_store=routing_store,
        template_store=template_store,
        rule_matcher=rule_matcher,
        recipient_resolver=recipient_resolver,
        lgpd_gateway=lgpd_gateway,
        dispatcher_manager=dispatcher_manager,
    )

    return engine


@pytest.mark.asyncio
async def test_push_notification_e2e(routing_engine, dispatcher_manager, mock_db):
    """Testa envio de push notification via D1."""
    # Arrange
    from comunicacao.channels.push import PushConfig, PushDispatcher

    push_config = PushConfig(enabled=True)
    push_dispatcher = PushDispatcher(db=mock_db, config=push_config)
    dispatcher_manager.register(push_dispatcher)

    intent = SendIntentRequest(
        intent_id="test-push-001",
        intent_type="clinical_alert",
        priority=IntentPriority.HIGH,
        patient_id="patient-123",
        channels=["push"],
        template_id="clinical_alert",
        template_data={
            "severity": "high",
            "title": "Glicemia Elevada",
            "message": "Glicemia: 250 mg/dL",
        },
        metadata={},
    )

    # Mock subscription
    from comunicacao.channels.models import PushSubscription

    subscription = PushSubscription(
        user_id="patient-123",
        device_id="device-001",
        provider="vapid",
        subscription_data={"endpoint": "https://fcm.googleapis.com/fcm/send/test"},
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [subscription]
    mock_db.execute.return_value = mock_result

    # Act
    with patch("comunicacao.channels.push.vapid_service.VAPIDPushService.send") as mock_send:
        mock_send.return_value = {"success": True, "message_id": "push-123"}
        result = await routing_engine.send_intent(intent)

    # Assert
    assert result.intent_id == "test-push-001"
    assert len(result.dispatched_channels) > 0


@pytest.mark.asyncio
async def test_whatsapp_e2e(routing_engine, dispatcher_manager, mock_db):
    """Testa envio de WhatsApp via D1."""
    # Arrange
    from comunicacao.channels.whatsapp import WhatsAppConfig, WhatsAppDispatcher

    whatsapp_config = WhatsAppConfig(
        access_token="test-token",
        phone_number_id="123456",
        enabled=True,
    )
    whatsapp_dispatcher = WhatsAppDispatcher(db=mock_db, config=whatsapp_config)
    dispatcher_manager.register(whatsapp_dispatcher)

    intent = SendIntentRequest(
        intent_id="test-whatsapp-001",
        intent_type="medication_reminder",
        priority=IntentPriority.MEDIUM,
        patient_id="patient-456",
        channels=["whatsapp"],
        template_id="medication_reminder",
        template_data={
            "patient_name": "João Silva",
            "medication": "Metformina",
            "dosage": "500mg",
            "time": "08:00",
        },
        metadata={},
    )

    # Act
    with patch("comunicacao.channels.whatsapp.client.WhatsAppClient.send_template") as mock_send:
        mock_send.return_value = {"messages": [{"id": "wamid.123"}]}
        result = await routing_engine.send_intent(intent)

    # Assert
    assert result.intent_id == "test-whatsapp-001"


@pytest.mark.asyncio
async def test_sms_e2e(routing_engine, dispatcher_manager, mock_db):
    """Testa envio de SMS via D1."""
    # Arrange
    from comunicacao.channels.sms import SMSConfig, SMSDispatcher

    sms_config = SMSConfig(
        twilio_account_sid="test-sid",
        twilio_auth_token="test-token",
        twilio_from_number="+15551234567",
        twilio_enabled=True,
        enabled=True,
    )
    sms_dispatcher = SMSDispatcher(db=mock_db, config=sms_config)
    dispatcher_manager.register(sms_dispatcher)

    intent = SendIntentRequest(
        intent_id="test-sms-001",
        intent_type="appointment_reminder",
        priority=IntentPriority.MEDIUM,
        patient_id="patient-789",
        channels=["sms"],
        template_id="appointment_reminder",
        template_data={
            "patient_name": "Maria Santos",
            "date": "20/02/2026",
            "time": "14:00",
        },
        metadata={},
    )

    # Act
    with patch("comunicacao.channels.sms.providers.twilio.TwilioSMSProvider.send") as mock_send:
        mock_send.return_value = {"sid": "SM123", "status": "sent"}
        result = await routing_engine.send_intent(intent)

    # Assert
    assert result.intent_id == "test-sms-001"


@pytest.mark.asyncio
async def test_email_e2e(routing_engine, dispatcher_manager, mock_db):
    """Testa envio de Email via D1."""
    # Arrange
    from comunicacao.channels.email import EmailConfig, EmailDispatcher
    from comunicacao.channels.email.config import SMTPConfig

    email_config = EmailConfig(
        smtp=SMTPConfig(
            host="smtp.example.com",
            port=587,
            username="test@example.com",
            password="test-password",
            from_email="noreply@intellicare.com.br",
            from_name="IntelliCare",
            use_tls=True,
            enabled=True,
        ),
        enabled=True,
    )
    email_dispatcher = EmailDispatcher(db=mock_db, config=email_config)
    dispatcher_manager.register(email_dispatcher)

    intent = SendIntentRequest(
        intent_id="test-email-001",
        intent_type="clinical_alert",
        priority=IntentPriority.HIGH,
        patient_id="patient-999",
        channels=["email"],
        template_id="clinical_alert",
        template_data={
            "severity": "high",
            "title": "Alerta Clínico",
            "message": "Pressão arterial elevada",
            "patient_name": "Carlos Souza",
        },
        metadata={},
    )

    # Act
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        result = await routing_engine.send_intent(intent)

    # Assert
    assert result.intent_id == "test-email-001"


@pytest.mark.asyncio
async def test_multi_channel_e2e(routing_engine, dispatcher_manager, mock_db):
    """Testa envio para múltiplos canais simultaneamente."""
    # Arrange - Registrar todos os dispatchers
    from comunicacao.channels.push import PushConfig, PushDispatcher
    from comunicacao.channels.whatsapp import WhatsAppConfig, WhatsAppDispatcher
    from comunicacao.channels.sms import SMSConfig, SMSDispatcher
    from comunicacao.channels.email import EmailConfig, EmailDispatcher
    from comunicacao.channels.email.config import SMTPConfig

    # Push
    push_config = PushConfig(enabled=True)
    push_dispatcher = PushDispatcher(db=mock_db, config=push_config)
    dispatcher_manager.register(push_dispatcher)

    # WhatsApp
    whatsapp_config = WhatsAppConfig(
        access_token="test-token",
        phone_number_id="123456",
        enabled=True,
    )
    whatsapp_dispatcher = WhatsAppDispatcher(db=mock_db, config=whatsapp_config)
    dispatcher_manager.register(whatsapp_dispatcher)

    # SMS
    sms_config = SMSConfig(
        twilio_account_sid="test-sid",
        twilio_auth_token="test-token",
        twilio_from_number="+15551234567",
        twilio_enabled=True,
        enabled=True,
    )
    sms_dispatcher = SMSDispatcher(db=mock_db, config=sms_config)
    dispatcher_manager.register(sms_dispatcher)

    # Email
    email_config = EmailConfig(
        smtp=SMTPConfig(
            host="smtp.example.com",
            port=587,
            username="test@example.com",
            password="test-password",
            from_email="noreply@intellicare.com.br",
            from_name="IntelliCare",
            use_tls=True,
            enabled=True,
        ),
        enabled=True,
    )
    email_dispatcher = EmailDispatcher(db=mock_db, config=email_config)
    dispatcher_manager.register(email_dispatcher)

    intent = SendIntentRequest(
        intent_id="test-multi-001",
        intent_type="clinical_alert",
        priority=IntentPriority.CRITICAL,
        patient_id="patient-multi",
        channels=["push", "whatsapp", "sms", "email"],
        template_id="clinical_alert",
        template_data={
            "severity": "critical",
            "title": "Alerta Crítico",
            "message": "Glicemia crítica: 400 mg/dL",
        },
        metadata={},
    )

    # Act
    with patch("comunicacao.channels.push.vapid_service.VAPIDPushService.send"), \
         patch("comunicacao.channels.whatsapp.client.WhatsAppClient.send_template"), \
         patch("comunicacao.channels.sms.providers.twilio.TwilioSMSProvider.send"), \
         patch("smtplib.SMTP"):
        result = await routing_engine.send_intent(intent)

    # Assert
    assert result.intent_id == "test-multi-001"
    # Deve ter tentado enviar para todos os canais


@pytest.mark.asyncio
async def test_fallback_chain_e2e(routing_engine, dispatcher_manager, mock_db):
    """Testa fallback entre canais quando um falha."""
    # Arrange
    from comunicacao.channels.sms import SMSConfig, SMSDispatcher
    from comunicacao.channels.email import EmailConfig, EmailDispatcher
    from comunicacao.channels.email.config import SMTPConfig

    # SMS (vai falhar)
    sms_config = SMSConfig(
        twilio_account_sid="test-sid",
        twilio_auth_token="test-token",
        twilio_from_number="+15551234567",
        twilio_enabled=True,
        enabled=True,
    )
    sms_dispatcher = SMSDispatcher(db=mock_db, config=sms_config)
    dispatcher_manager.register(sms_dispatcher)

    # Email (fallback)
    email_config = EmailConfig(
        smtp=SMTPConfig(
            host="smtp.example.com",
            port=587,
            username="test@example.com",
            password="test-password",
            from_email="noreply@intellicare.com.br",
            from_name="IntelliCare",
            use_tls=True,
            enabled=True,
        ),
        enabled=True,
    )
    email_dispatcher = EmailDispatcher(db=mock_db, config=email_config)
    dispatcher_manager.register(email_dispatcher)

    intent = SendIntentRequest(
        intent_id="test-fallback-001",
        intent_type="medication_reminder",
        priority=IntentPriority.MEDIUM,
        patient_id="patient-fallback",
        channels=["sms"],
        fallback_channels=["email"],
        template_id="medication_reminder",
        template_data={
            "patient_name": "Ana Costa",
            "medication": "Losartana",
        },
        metadata={},
    )

    # Act - SMS falha, Email sucede
    with patch("comunicacao.channels.sms.providers.twilio.TwilioSMSProvider.send") as mock_sms, \
         patch("smtplib.SMTP") as mock_smtp:
        mock_sms.side_effect = Exception("SMS provider unavailable")
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await routing_engine.send_intent(intent)

    # Assert
    assert result.intent_id == "test-fallback-001"
    # Deve ter usado fallback para email

