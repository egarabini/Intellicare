"""FastAPI app do modulo de comunicacao."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from comunicacao.api.case_room_routes import create_case_room_router
from comunicacao.api.channel_routes import create_channel_router
from comunicacao.api.health_routes import router as health_router
from comunicacao.api.lgpd_routes import router as lgpd_router
from comunicacao.api.rocketchat_routes import router as rocketchat_router
from comunicacao.api.routing_routes import create_routing_router
from comunicacao.api.template_routes import create_template_router
from comunicacao.config import ComunicacaoConfig
from comunicacao.dispatchers import create_default_dispatcher_manager
from comunicacao.events.redis_consumer import RedisAlertConsumer
from comunicacao.matrix_client import MatrixClientService
from comunicacao.routing.delayed import DelayedWorker, InMemoryDelayedScheduler, RedisDelayedScheduler
from comunicacao.routing.engine import RoutingEngine, RoutingService
from comunicacao.storage import (
    PatientRoomRepository,
    build_patient_room_repository,
    build_routing_rule_store,
    build_routing_store,
    build_template_store,
)
from comunicacao.templates.renderer import TemplateRenderer
from comunicacao.templates.seed_loader import ensure_seed_templates

_state: dict[str, Any] = {}
logger = logging.getLogger(__name__)


class SendMessageRequest(BaseModel):
    room_id: str | None = Field(default=None, description="Room Matrix no formato !abc:dominio")
    message: str = Field(min_length=1, max_length=4000)


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    topic: str | None = Field(default=None, max_length=500)
    is_direct: bool = False
    invite: list[str] = Field(default_factory=list)


class InviteUserRequest(BaseModel):
    user_id: str = Field(min_length=3, description="Usuario Matrix no formato @usuario:dominio")


class BotStartRequest(BaseModel):
    help_message: str | None = Field(default=None, max_length=800)


class PatientRoomLinkRequest(BaseModel):
    patient_id: str = Field(min_length=1, max_length=120)
    room_id: str = Field(min_length=1, description="Room Matrix no formato !abc:dominio")


class ClinicalAlertEventRequest(BaseModel):
    patient_id: str = Field(min_length=1, max_length=120)
    source_module: str = Field(min_length=1, max_length=120)
    alert_type: str = Field(min_length=1, max_length=120)
    severity: str = Field(min_length=1, max_length=30)
    message: str = Field(min_length=1, max_length=3000)
    room_id: str | None = Field(default=None, description="Opcional: sobrescreve rota por paciente")
    correlation_id: str | None = Field(default=None, max_length=120)


def _format_clinical_alert_message(payload: ClinicalAlertEventRequest) -> str:
    correlation = payload.correlation_id or "-"
    return (
        f"[ALERTA CLINICO] {payload.severity.upper()}\n"
        f"Paciente: {payload.patient_id}\n"
        f"Origem: {payload.source_module}\n"
        f"Tipo: {payload.alert_type}\n"
        f"Mensagem: {payload.message}\n"
        f"Correlacao: {correlation}"
    )


async def _dispatch_clinical_alert(payload: ClinicalAlertEventRequest) -> dict[str, Any]:
    config: ComunicacaoConfig = _state["config"]
    matrix = _require_matrix_service()
    repository: PatientRoomRepository = _state["repository"]

    room_id = payload.room_id or repository.get_room_id(payload.patient_id) or config.matrix_default_room_id
    if not room_id:
        raise HTTPException(
            status_code=400,
            detail="sem room_id: informe no payload, crie vinculo patient-room ou configure MATRIX_DEFAULT_ROOM_ID",
        )

    message = _format_clinical_alert_message(payload)
    result = await matrix.send_text_message(room_id=room_id, message=message)
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail=result.get("error", "falha ao enviar alerta clinico"))

    return {
        "ok": True,
        "patient_id": payload.patient_id,
        "room_id": room_id,
        "source_module": payload.source_module,
        "alert_type": payload.alert_type,
        "severity": payload.severity,
        "event_id": result.get("event_id"),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    config = ComunicacaoConfig()
    matrix: MatrixClientService | None = None
    dispatcher_manager = create_default_dispatcher_manager()
    if config.matrix_enable_legacy_stack:
        matrix = MatrixClientService(config)

    # Registrar JitsiDispatcher (EF-COM-020 — aguarda comunicacao.jitsi)
    try:
        from comunicacao.jitsi import JitsiConfig, JitsiDispatcher  # noqa: PLC0415
        from comunicacao.storage.repository import get_db_session  # noqa: PLC0415
        jitsi_config = JitsiConfig.from_env()
        async with get_db_session() as db:
            jitsi_dispatcher = JitsiDispatcher(db=db, config=jitsi_config)
            dispatcher_manager.register(jitsi_dispatcher)
            logger.info("JitsiDispatcher registrado (D3)")
    except Exception as exc:
        logger.warning("JitsiDispatcher não disponível (Jitsi não configurado): %s", exc)

    # Registrar PushDispatcher (D4.2 - Push Notifications)
    try:
        from comunicacao.channels.push import PushConfig, PushDispatcher  # noqa: PLC0415
        from comunicacao.storage.repository import get_db_session  # noqa: PLC0415
        push_config = PushConfig.from_env()
        async with get_db_session() as db:
            push_dispatcher = PushDispatcher(db=db, config=push_config)
            dispatcher_manager.register(push_dispatcher)
            logger.info("PushDispatcher registrado (D4.2 - VAPID/FCM)")
    except Exception as exc:
        logger.warning("PushDispatcher não disponível (Push não configurado): %s", exc)

    # Registrar WhatsAppDispatcher (D4.3 - WhatsApp Business API)
    try:
        from comunicacao.channels.whatsapp import WhatsAppConfig, WhatsAppDispatcher  # noqa: PLC0415
        from comunicacao.storage.repository import get_db_session  # noqa: PLC0415
        whatsapp_config = WhatsAppConfig.from_env()
        async with get_db_session() as db:
            whatsapp_dispatcher = WhatsAppDispatcher(db=db, config=whatsapp_config)
            dispatcher_manager.register(whatsapp_dispatcher)
            logger.info("WhatsAppDispatcher registrado (D4.3 - Meta Graph API)")
    except Exception as exc:
        logger.warning("WhatsAppDispatcher não disponível (WhatsApp não configurado): %s", exc)

    # Registrar SMSDispatcher (D4.4 - SMS Twilio/Zenvia)
    try:
        from comunicacao.channels.sms import SMSConfig, SMSDispatcher  # noqa: PLC0415
        from comunicacao.storage.repository import get_db_session  # noqa: PLC0415
        sms_config = SMSConfig.from_env()
        async with get_db_session() as db:
            sms_dispatcher = SMSDispatcher(db=db, config=sms_config)
            dispatcher_manager.register(sms_dispatcher)
            logger.info("SMSDispatcher registrado (D4.4 - Twilio/Zenvia/SNS)")
    except Exception as exc:
        logger.warning("SMSDispatcher não disponível (SMS não configurado): %s", exc)

    # Registrar EmailDispatcher (D4.5 - Email SMTP)
    try:
        from comunicacao.channels.email import EmailConfig, EmailDispatcher  # noqa: PLC0415
        from comunicacao.storage.repository import get_db_session  # noqa: PLC0415
        email_config = EmailConfig.from_env()
        async with get_db_session() as db:
            email_dispatcher = EmailDispatcher(db=db, config=email_config)
            dispatcher_manager.register(email_dispatcher)
            logger.info("EmailDispatcher registrado (D4.5 - SMTP)")
    except Exception as exc:
        logger.warning("EmailDispatcher não disponível (Email não configurado): %s", exc)

    consumer = RedisAlertConsumer(config=config, on_alert=_on_alert_event)
    repository = build_patient_room_repository(database_url=config.database_url, schema=config.database_schema)
    delayed_scheduler = InMemoryDelayedScheduler()
    if config.redis_url:
        try:
            delayed_scheduler = RedisDelayedScheduler(
                redis_url=config.redis_url,
                queue_key=config.routing_delayed_queue_key,
            )
        except Exception:
            delayed_scheduler = InMemoryDelayedScheduler()
    routing_store = build_routing_store(
        database_url=config.database_url,
        schema=config.routing_operational_schema,
    )
    rule_store = build_routing_rule_store(
        database_url=config.database_url,
        schema=config.routing_operational_schema,
    )
    template_store = build_template_store(
        database_url=config.database_url,
        schema=config.routing_operational_schema,
    )

    from comunicacao.routing.lgpd import DefaultLGPDGateway
    from comunicacao.routing.recipient_resolver import RecipientResolver
    from comunicacao.routing.rule_matcher import RuleMatcher

    rule_matcher = RuleMatcher(rule_store=rule_store)
    recipient_resolver = RecipientResolver(room_repository=repository)
    lgpd_gateway = DefaultLGPDGateway()

    routing_engine = RoutingEngine(
        routing_store=routing_store,
        template_store=template_store,
        rule_matcher=rule_matcher,
        recipient_resolver=recipient_resolver,
        lgpd_gateway=lgpd_gateway,
        dispatcher_manager=dispatcher_manager,
    )
    routing_service = routing_engine  # RoutingService is an alias for RoutingEngine

    delayed_worker = DelayedWorker(
        scheduler=delayed_scheduler,
        on_task=lambda task: routing_service.send_intent(task.payload)
        if hasattr(routing_service, "send_intent")
        else None,
        poll_seconds=config.routing_delayed_poll_seconds,
    )
    template_renderer = TemplateRenderer()

    # Carregar templates seed (não sobrescreve existentes)
    ensure_seed_templates(template_store)
    logger.info("Templates seed carregados")

    # EF-COM-021: Sala de Caso Multidisciplinar
    import os
    from comunicacao.case_room.store import CaseRoomStore
    from comunicacao.case_room.service import CaseRoomService
    from comunicacao.rocketchat.channel_service import RocketChatChannelService
    from comunicacao.rocketchat.client import RocketChatClient
    from comunicacao.rocketchat.config import RocketChatConfig

    case_room_store = CaseRoomStore()
    case_room_service: CaseRoomService | None = None
    try:
        rc_config = RocketChatConfig.from_env()
        rc_client_for_case = RocketChatClient(rc_config)
        rc_channel_svc = RocketChatChannelService(client=rc_client_for_case, config=rc_config)
        case_room_service = CaseRoomService(
            channel_service=rc_channel_svc,
            rc_client=rc_client_for_case,
            store=case_room_store,
            jitsi_url=os.getenv("JITSI_URL", "https://meet.gsi.srv.br"),
        )
        logger.info("CaseRoomService inicializado (EF-COM-021)")
    except Exception as exc:
        logger.warning("CaseRoomService não disponível (RC não configurado): %s", exc)

    _state["config"] = config
    _state["matrix"] = matrix
    _state["dispatcher_manager"] = dispatcher_manager
    _state["routing_service"] = routing_service
    _state["routing_delayed_scheduler"] = delayed_scheduler
    _state["routing_delayed_worker"] = delayed_worker
    _state["consumer"] = consumer
    _state["repository"] = repository
    _state["template_store"] = template_store
    _state["template_renderer"] = template_renderer
    _state["case_room_store"] = case_room_store
    _state["case_room_service"] = case_room_service
    _state["event_metrics"] = {
        "received": 0,
        "routed_ok": 0,
        "routed_error": 0,
        "last_error": None,
        "last_event": None,
    }

    if config.matrix_enable_event_consumer:
        await consumer.start()
        # Atualizar métrica de status do consumer
        from comunicacao.metrics import set_redis_consumer_status
        set_redis_consumer_status(True)
    if config.routing_enable_delayed_worker:
        await delayed_worker.start()

    yield

    await consumer.stop()
    # Atualizar métrica de status do consumer
    from comunicacao.metrics import set_redis_consumer_status
    set_redis_consumer_status(False)

    await delayed_worker.stop()
    repository.close()
    if matrix is not None:
        await matrix.logout()
        await matrix.close()


def create_app() -> FastAPI:
    from .sms_routes import router as sms_router
    from .email_routes import router as email_router

    app = FastAPI(
        title="IntelliCare Communication Module",
        description="Microservice for handling multi-channel communications (SMS, Email, WhatsApp).",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register Routers
    app.include_router(sms_router, prefix="/api/v1")
    app.include_router(email_router, prefix="/api/v1")

    # Register simple health/info endpoints FIRST so they take priority over health_router
    @app.get("/api/v1/health")
    async def health() -> dict[str, Any]:
        config: ComunicacaoConfig = _state["config"]
        matrix = _state.get("matrix")

        matrix_status = "not_checked"
        if config.matrix_enable_legacy_stack:
            if matrix is None:
                matrix_status = "disabled"
            elif config.matrix_enable_health_login_check:
                matrix_status = "ok" if await matrix.ensure_login() else "degraded"

        status = "healthy" if matrix_status in {"ok", "not_checked", "disabled"} else "degraded"
        return {
            "status": status,
            "module_name": config.module_name,
            "version": config.module_version,
            "matrix": matrix_status,
            "matrix_legacy_enabled": config.matrix_enable_legacy_stack,
        }

    @app.get("/api/v1/info")
    def info() -> dict[str, Any]:
        config: ComunicacaoConfig = _state["config"]
        return {
            "name": config.module_name,
            "version": config.module_version,
            "description": "Comunicacao omnichannel para pacientes, equipe e agentes",
            "capabilities": [
                "routing-engine",
                "rocketchat",
                "email",
                "sms",
                "whatsapp",
                "push",
                "geralda-bot",
                "patient-room-linking",
                "clinical-alert-routing",
                "redis-stream-consumer",
            ] + (
                ["matrix-login", "matrix-room-send", "matrix-room-create", "matrix-room-invite"]
                if config.matrix_enable_legacy_stack
                else []
            ),
        }

    app.include_router(create_channel_router(lambda: _state))
    app.include_router(create_routing_router(lambda: _state))
    app.include_router(create_template_router(lambda: _state))
    app.include_router(create_case_room_router(lambda: _state))
    app.include_router(rocketchat_router)
    app.include_router(health_router)
    app.include_router(lgpd_router)

    # Jitsi routes (EF-COM-020 — aguarda comunicacao.jitsi)
    try:
        from comunicacao.api.jitsi_routes import router as jitsi_router
        app.include_router(jitsi_router)
    except ImportError:
        logger.warning("jitsi_routes não disponível (comunicacao.jitsi não instalado)")

    # Adicionar middleware de métricas
    from comunicacao.monitoring.middleware import MetricsMiddleware
    app.add_middleware(MetricsMiddleware)

    @app.get("/metrics")
    def metrics() -> Any:
        """
        Endpoint Prometheus para coleta de métricas.

        Expõe todas as métricas coletadas pelo módulo de comunicação:
        - comm_messages_total: Total de mensagens processadas
        - comm_channel_fallback_total: Total de fallbacks entre canais
        - comm_lgpd_blocked_total: Total de comunicações bloqueadas por LGPD
        - comm_lgpd_override_total: Total de overrides LGPD
        - comm_bot_commands_total: Total de comandos do bot executados
        - comm_events_processed_total: Total de eventos Redis processados
        - comm_message_latency_seconds: Latência de envio de mensagem
        - comm_api_request_duration_seconds: Duração de requisições HTTP
        - comm_db_connections_active: Conexões ativas ao PostgreSQL
        - comm_redis_connections_active: Conexões ativas ao Redis
        - comm_pending_intents: Intents pendentes de processamento
        - comm_dispatcher_health: Health status dos dispatchers
        """
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from fastapi.responses import Response

        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/api/v1/messages/send")
    async def send_message(payload: SendMessageRequest) -> dict[str, Any]:
        config: ComunicacaoConfig = _state["config"]
        matrix = _require_matrix_service()

        room_id = payload.room_id or config.matrix_default_room_id
        if not room_id:
            raise HTTPException(status_code=400, detail="room_id nao informado e MATRIX_DEFAULT_ROOM_ID vazio")

        result = await matrix.send_text_message(room_id=room_id, message=payload.message)
        if not result.get("ok"):
            raise HTTPException(status_code=502, detail=result.get("error", "falha ao enviar mensagem"))

        return result

    @app.post("/api/v1/rooms")
    async def create_room(payload: CreateRoomRequest) -> dict[str, Any]:
        matrix = _require_matrix_service()
        result = await matrix.create_room(
            name=payload.name,
            topic=payload.topic,
            is_direct=payload.is_direct,
            invite=payload.invite,
        )
        if not result.get("ok"):
            raise HTTPException(status_code=502, detail=result.get("error", "falha ao criar sala"))
        return result

    @app.post("/api/v1/rooms/{room_id}/invite")
    async def invite_user(room_id: str, payload: InviteUserRequest) -> dict[str, Any]:
        matrix = _require_matrix_service()
        result = await matrix.invite_user_to_room(room_id=room_id, user_id=payload.user_id)
        if not result.get("ok"):
            raise HTTPException(status_code=502, detail=result.get("error", "falha ao convidar usuario"))
        return result

    @app.get("/api/v1/bot/status")
    def bot_status() -> dict[str, Any]:
        matrix = _require_matrix_service()
        return matrix.bot_status()

    @app.post("/api/v1/bot/start")
    async def bot_start(payload: BotStartRequest) -> dict[str, Any]:
        matrix = _require_matrix_service()
        result = await matrix.start_bot(help_message=payload.help_message)
        if not result.get("ok"):
            raise HTTPException(status_code=502, detail=result.get("error", "falha ao iniciar bot"))
        return result

    @app.post("/api/v1/bot/stop")
    async def bot_stop() -> dict[str, Any]:
        matrix = _require_matrix_service()
        result = await matrix.stop_bot()
        if not result.get("ok"):
            raise HTTPException(status_code=502, detail=result.get("error", "falha ao parar bot"))
        return result

    @app.post("/api/v1/links/patient-room")
    def upsert_patient_room_link(payload: PatientRoomLinkRequest) -> dict[str, Any]:
        repository: PatientRoomRepository = _state["repository"]
        repository.upsert_link(payload.patient_id, payload.room_id)
        return {"ok": True, "patient_id": payload.patient_id, "room_id": payload.room_id}

    @app.get("/api/v1/links/patient-room/{patient_id}")
    def get_patient_room_link(patient_id: str) -> dict[str, Any]:
        repository: PatientRoomRepository = _state["repository"]
        room_id = repository.get_room_id(patient_id)
        if not room_id:
            raise HTTPException(status_code=404, detail=f"vinculo nao encontrado para patient_id={patient_id}")
        return {"ok": True, "patient_id": patient_id, "room_id": room_id}

    @app.get("/api/v1/links/patient-room")
    def list_patient_room_links(
        limit: int = Query(default=50, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        repository: PatientRoomRepository = _state["repository"]
        links = repository.list_links(limit=limit, offset=offset)
        return {"ok": True, "count": len(links), "limit": limit, "offset": offset, "items": links}

    @app.delete("/api/v1/links/patient-room/{patient_id}")
    def delete_patient_room_link(patient_id: str) -> dict[str, Any]:
        repository: PatientRoomRepository = _state["repository"]
        deleted = repository.delete_link(patient_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"vinculo nao encontrado para patient_id={patient_id}")
        return {"ok": True, "patient_id": patient_id, "deleted": True}

    @app.post("/api/v1/events/clinical-alert")
    async def route_clinical_alert(payload: ClinicalAlertEventRequest) -> dict[str, Any]:
        return await _dispatch_clinical_alert(payload)

    @app.get("/api/v1/events/consumer/status")
    def event_consumer_status() -> dict[str, Any]:
        consumer: RedisAlertConsumer = _state["consumer"]
        return consumer.status()

    @app.post("/api/v1/events/consumer/start")
    async def event_consumer_start() -> dict[str, Any]:
        consumer: RedisAlertConsumer = _state["consumer"]
        return await consumer.start()

    @app.post("/api/v1/events/consumer/stop")
    async def event_consumer_stop() -> dict[str, Any]:
        consumer: RedisAlertConsumer = _state["consumer"]
        return await consumer.stop()

    @app.get("/api/v1/events/metrics")
    def event_metrics() -> dict[str, Any]:
        return {"ok": True, **_state.get("event_metrics", {})}

    @app.post("/api/v1/events/metrics/reset")
    def event_metrics_reset() -> dict[str, Any]:
        _state["event_metrics"] = {
            "received": 0,
            "routed_ok": 0,
            "routed_error": 0,
            "last_error": None,
            "last_event": None,
        }
        return {"ok": True}

    return app


async def _on_alert_event(event_payload: dict[str, Any]) -> None:
    """Callback do consumidor Redis para rotear alertas via RoutingEngine."""
    from comunicacao.routing.models import CommunicationIntentCreate, RecipientType
    from comunicacao.metrics import track_redis_event

    metrics = _state.get("event_metrics")
    if isinstance(metrics, dict):
        metrics["received"] = int(metrics.get("received", 0)) + 1
        metrics["last_event"] = event_payload

    try:
        # Registrar evento Redis recebido
        track_redis_event(
            event_type=event_payload.get("alert_type", "clinical_alert"), status="received"
        )
        # Criar CommunicationIntent a partir do evento Redis
        intent_create = CommunicationIntentCreate(
            source_module=event_payload.get("source_module", "unknown"),
            source_event_id=event_payload.get("event_id"),  # ID do evento Redis
            recipient_type=RecipientType.PATIENT,
            recipient_id=event_payload["patient_id"],
            severity=event_payload.get("severity", "medium"),
            category=event_payload.get("alert_type", "clinical_alert"),
            correlation_id=event_payload.get("correlation_id", f"redis-{event_payload.get('patient_id', 'unknown')}"),
            content_raw=event_payload["message"],
            metadata={
                "event_type": "redis_stream_alert",
                "original_room_id": event_payload.get("room_id"),
            },
        )

        # Rotear via RoutingEngine
        routing_service: RoutingService = _state["routing_service"]
        intent = await routing_service.send_intent(intent_create)

        if isinstance(metrics, dict):
            metrics["routed_ok"] = int(metrics.get("routed_ok", 0)) + 1

        # Registrar evento Redis processado com sucesso
        track_redis_event(
            event_type=event_payload.get("alert_type", "clinical_alert"), status="processed"
        )

        logger.info(
            "Evento Redis roteado com sucesso: intent_id=%s, patient_id=%s, severity=%s",
            intent.id,
            event_payload["patient_id"],
            event_payload.get("severity", "medium"),
        )
    except KeyError as exc:
        # Campos obrigatórios faltando no payload
        if isinstance(metrics, dict):
            metrics["routed_error"] = int(metrics.get("routed_error", 0)) + 1
            metrics["last_error"] = f"Campo obrigatório faltando: {exc}"

        # Registrar evento Redis com erro
        track_redis_event(
            event_type=event_payload.get("alert_type", "unknown"), status="failed"
        )

        logger.warning("Evento Redis com campos faltando: %s", exc)
    except Exception as exc:  # pragma: no cover - guard runtime
        if isinstance(metrics, dict):
            metrics["routed_error"] = int(metrics.get("routed_error", 0)) + 1
            metrics["last_error"] = str(exc)

        # Registrar evento Redis com erro
        track_redis_event(
            event_type=event_payload.get("alert_type", "unknown"), status="failed"
        )

        logger.error("Falha ao processar evento Redis: %s", exc, exc_info=True)


def _require_matrix_service() -> MatrixClientService:
    matrix = _state.get("matrix")
    if matrix is None:
        raise HTTPException(
            status_code=503,
            detail="stack Matrix legada desabilitada",
        )
    return matrix
