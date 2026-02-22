"""Engine principal de roteamento de comunicações - Fase 2."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from comunicacao.routing.models import (
    CommunicationIntentCreate,
    CommunicationIntentRecord,
    IntentStatus,
    TimelineEvent,
)

if TYPE_CHECKING:
    from comunicacao.dispatchers.base import DispatcherManager
    from comunicacao.routing.fallback_monitor import FallbackMonitor
    from comunicacao.routing.lgpd import LGPDComplianceGateway
    from comunicacao.routing.recipient_resolver import RecipientResolver
    from comunicacao.routing.rule_matcher import RuleMatcher
    from comunicacao.storage.routing_repository import RoutingStore
    from comunicacao.storage.template_repository import TemplateStore
    from comunicacao.templates.renderer import TemplateRenderer

logger = logging.getLogger(__name__)


class RoutingEngine:
    """
    Engine principal de roteamento - Fase 3 (com Fallback).

    Pipeline:
    1. Validar intent
    2. Resolver destinatário (RecipientResolver)
    3. Verificar LGPD (LGPDComplianceGateway)
    4. Aplicar regras (RuleMatcher)
    5. Renderizar conteúdo (TemplateStore)
    6. Despachar com fallback (FallbackMonitor)
    7. Monitorar e atualizar timeline
    """

    def __init__(
        self,
        routing_store: RoutingStore,
        template_store: TemplateStore,
        rule_matcher: RuleMatcher,
        recipient_resolver: RecipientResolver,
        lgpd_gateway: LGPDComplianceGateway,
        dispatcher_manager: DispatcherManager,
        template_renderer: TemplateRenderer | None = None,
        fallback_monitor: FallbackMonitor | None = None,
    ) -> None:
        self.routing_store = routing_store
        self.template_store = template_store
        self.rule_matcher = rule_matcher
        self.recipient_resolver = recipient_resolver
        self.lgpd_gateway = lgpd_gateway
        self.dispatcher_manager = dispatcher_manager
        self.fallback_monitor = fallback_monitor

        # Se template_renderer não foi fornecido, cria um padrão
        if template_renderer is None:
            from comunicacao.templates.renderer import TemplateRenderer
            template_renderer = TemplateRenderer()
        self.template_renderer = template_renderer

        # Se fallback_monitor não foi fornecido, cria um padrão
        if self.fallback_monitor is None:
            from comunicacao.routing.fallback_monitor import FallbackMonitor
            self.fallback_monitor = FallbackMonitor(
                routing_store=routing_store,
                dispatcher_manager=dispatcher_manager,
            )

    async def create_intent(self, intent_create: CommunicationIntentCreate) -> CommunicationIntentRecord:
        """
        Cria nova intenção de comunicação.

        Retorna o registro criado com timeline inicial.
        """
        # Idempotência: verifica se já existe intent com mesmo source_module+source_event_id
        if intent_create.source_event_id:
            existing = self.routing_store.find_by_source_event(
                source_module=intent_create.source_module,
                source_event_id=intent_create.source_event_id,
            )
            if existing is not None:
                logger.info(
                    "RoutingEngine: intent idempotente encontrado (source=%s, event_id=%s, id=%s)",
                    intent_create.source_module,
                    intent_create.source_event_id,
                    existing.id,
                )
                return existing

        # Cria record a partir do create
        intent = CommunicationIntentRecord(
            **intent_create.model_dump(exclude_unset=True),
            status=IntentStatus.PENDING,
            timeline=[
                TimelineEvent(
                    event_type="intent_created",
                    details={
                        "source_module": intent_create.source_module,
                        "severity": intent_create.severity,
                        "category": intent_create.category,
                    },
                )
            ],
        )

        # Persiste
        self.routing_store.save_intent(intent)

        logger.info(
            "RoutingEngine: intent %s criado (source=%s, severity=%s, category=%s)",
            intent.id,
            intent.source_module,
            intent.severity,
            intent.category,
        )

        return intent

    async def process_intent(self, intent_id: UUID) -> CommunicationIntentRecord:
        """
        Processa uma intenção de comunicação através do pipeline completo.

        Pipeline:
        1. Carregar intent
        2. Resolver destinatário
        3. Verificar LGPD
        4. Aplicar regras
        5. Renderizar conteúdo
        6. Despachar
        7. Atualizar status
        """
        # 1. Carregar intent
        intent = self.routing_store.get_intent(str(intent_id))
        if not intent:
            raise ValueError(f"Intent {intent_id} não encontrado")

        # Atualiza status para PROCESSING
        intent.status = IntentStatus.PROCESSING
        intent.updated_at = datetime.now(UTC)
        self._append_timeline(intent, "processing_started", {})
        self.routing_store.save_intent(intent)

        try:
            # 2. Resolver destinatário
            resolved_recipient = await self.recipient_resolver.resolve(
                recipient_type=intent.recipient_type,
                recipient_id=intent.recipient_id,
            )
            self._append_timeline(intent, "recipient_resolved", {
                "recipient_type": intent.recipient_type.value,
                "recipient_id": intent.recipient_id,
            })

            # 3. Verificar LGPD
            lgpd_approved = await self.lgpd_gateway.check_compliance(
                intent=intent,
                resolved_recipient=resolved_recipient,
            )
            self._append_timeline(intent, "lgpd_checked", {"approved": lgpd_approved})

            if not lgpd_approved:
                intent.status = IntentStatus.FAILED
                self._append_timeline(intent, "lgpd_blocked", {})
                self.routing_store.save_intent(intent)
                logger.warning("RoutingEngine: intent %s bloqueado por LGPD", intent.id)
                return intent

            # 4. Aplicar regras
            channels = self.rule_matcher.get_channel_sequence(intent)
            if not channels:
                intent.status = IntentStatus.FAILED
                self._append_timeline(intent, "no_rules_matched", {})
                self.routing_store.save_intent(intent)
                logger.warning("RoutingEngine: intent %s sem regras correspondentes", intent.id)
                return intent

            self._append_timeline(intent, "rules_matched", {"channels": channels})

            # 5. Renderizar conteúdo
            # Se tem template_id, renderiza o template para cada canal
            # Caso contrário, usa content_raw diretamente
            if intent.content_template_id:
                try:
                    template = self.template_store.get(intent.content_template_id)
                    if template is None:
                        raise ValueError(f"Template não encontrado: {intent.content_template_id}")

                    # Valida parâmetros
                    params = intent.content_params or {}
                    validation_errors = self.template_renderer.validate(template, params)
                    if validation_errors:
                        raise ValueError(f"Parâmetros inválidos: {', '.join(validation_errors)}")

                    # Renderiza para o primeiro canal (será usado pelo dispatcher)
                    # O dispatcher pode re-renderizar para outros canais se necessário
                    first_channel = channels[0]
                    rendered = self.template_renderer.render(template, first_channel, params)

                    # Armazena o conteúdo renderizado em content_raw para uso posterior
                    intent.content_raw = rendered.get("body", "")

                    self._append_timeline(intent, "template_rendered", {
                        "template_id": intent.content_template_id,
                        "channel": first_channel,
                        "params_count": len(params),
                    })

                except Exception as exc:
                    logger.error("RoutingEngine: erro ao renderizar template %s: %s",
                                intent.content_template_id, exc)
                    intent.status = IntentStatus.FAILED
                    self._append_timeline(intent, "template_render_failed", {
                        "template_id": intent.content_template_id,
                        "error": str(exc),
                    })
                    self.routing_store.save_intent(intent)
                    return intent
            else:
                # Usa content_raw diretamente
                if not intent.content_raw:
                    logger.warning("RoutingEngine: intent %s sem conteúdo (template ou raw)", intent.id)
                    intent.content_raw = "Conteúdo não disponível"

                self._append_timeline(intent, "content_raw_used", {
                    "content_length": len(intent.content_raw),
                })

            # 6. Despachar com fallback automático (Fase 3)
            success, channel_used = await self.fallback_monitor.try_channel_sequence(
                intent=intent,
                channels=channels,
                resolved_recipient=resolved_recipient,
            )

            if success:
                # Verifica se houve fallback (tentativas com falha antes do sucesso)
                all_attempts = self.fallback_monitor.get_attempts(intent.id)
                failed_attempts = [a for a in all_attempts if not a.success]
                if failed_attempts and channel_used != channels[0]:
                    self._append_timeline(intent, "fallback_activated", {
                        "failed_channel": failed_attempts[0].channel,
                        "succeeded_channel": channel_used,
                    })
                self._append_timeline(intent, "dispatched", {
                    "channel": channel_used,
                    "attempts": len(self.fallback_monitor.get_attempts(intent.id)),
                })
                intent.status = IntentStatus.COMPLETED
            else:
                self._append_timeline(intent, "all_channels_failed", {
                    "channels": channels,
                    "attempts": len(self.fallback_monitor.get_attempts(intent.id)),
                })

                # Verificar se deve escalar
                if intent.severity in ["critical", "high"]:
                    escalation_id = await self.fallback_monitor.escalate(
                        intent=intent,
                        reason="all_channels_failed",
                    )
                    if escalation_id:
                        self._append_timeline(intent, "escalated", {
                            "escalation_intent_id": str(escalation_id),
                        })

                intent.status = IntentStatus.FAILED

            # Registra resultados de entrega
            attempts = self.fallback_monitor.get_attempts(intent.id)
            for attempt in attempts:
                from comunicacao.routing.models import DeliveryResultRecord, DeliveryStatus as RoutingDeliveryStatus
                delivery = DeliveryResultRecord(
                    intent_id=intent.id,
                    channel=attempt.channel,
                    attempt_number=attempt.attempt_number,
                    status=RoutingDeliveryStatus.SENT if attempt.success else RoutingDeliveryStatus.FAILED,
                    error_message=attempt.error_message if not attempt.success else None,
                )
                self.routing_store.append_delivery(delivery)

            # Limpa tentativas do monitor
            self.fallback_monitor.clear_attempts(intent.id)

            # Salva estado final
            intent.updated_at = datetime.now(UTC)
            self.routing_store.save_intent(intent)

            logger.info("RoutingEngine: intent %s processado - status: %s", intent.id, intent.status)
            return intent

        except Exception as exc:
            logger.exception("RoutingEngine: erro ao processar intent %s", intent.id)
            intent.status = IntentStatus.FAILED
            self._append_timeline(intent, "processing_failed", {"error": str(exc)})
            intent.updated_at = datetime.now(UTC)
            self.routing_store.save_intent(intent)
            raise

    def _append_timeline(self, intent: CommunicationIntentRecord, event_type: str, details: dict) -> None:
        """Adiciona evento à timeline (append-only)."""
        event = TimelineEvent(event_type=event_type, details=details)
        intent.timeline.append(event)

    async def send_intent(self, intent_create: CommunicationIntentCreate) -> CommunicationIntentRecord:
        """
        Cria e processa uma intenção de comunicação (método de conveniência).

        Este método combina create_intent() e process_intent() em uma única chamada,
        com tracking de métricas integrado.
        """
        from comunicacao.metrics import (
            comm_intent_received_total,
            comm_intent_completed_total,
            comm_intent_failed_total,
            comm_routing_latency_seconds,
        )
        import time

        # Registrar intent recebido
        comm_intent_received_total.labels(
            source_module=intent_create.source_module,
            severity=intent_create.severity,
            category=intent_create.category,
        ).inc()

        # Medir latência
        start_time = time.time()

        try:
            # Criar intent
            intent = await self.create_intent(intent_create)

            # Idempotency: se intent já foi processado, retorna sem reprocessar
            if intent.status != IntentStatus.PENDING:
                logger.info(
                    "RoutingEngine.send_intent: intent %s ja processado (status=%s) - retornando sem reprocessar",
                    intent.id,
                    intent.status,
                )
                return intent

            # Processar intent
            result = await self.process_intent(intent.id)

            # Sucesso: registrar latência e incrementar contador
            latency = time.time() - start_time
            comm_routing_latency_seconds.labels(
                severity=intent_create.severity,
                category=intent_create.category,
            ).observe(latency)

            if result.status == IntentStatus.COMPLETED:
                comm_intent_completed_total.labels(
                    source_module=intent_create.source_module,
                    severity=intent_create.severity,
                    category=intent_create.category,
                ).inc()
            else:
                comm_intent_failed_total.labels(
                    source_module=intent_create.source_module,
                    severity=intent_create.severity,
                    category=intent_create.category,
                    reason=result.status.value,
                ).inc()

            logger.info(
                "RoutingEngine.send_intent: intent %s processado em %.3fs - status: %s",
                result.id,
                latency,
                result.status.value,
            )

            return result

        except Exception as exc:
            # Falha: registrar latência e incrementar contador de falhas
            latency = time.time() - start_time
            comm_routing_latency_seconds.labels(
                severity=intent_create.severity,
                category=intent_create.category,
            ).observe(latency)

            comm_intent_failed_total.labels(
                source_module=intent_create.source_module,
                severity=intent_create.severity,
                category=intent_create.category,
                reason=type(exc).__name__,
            ).inc()

            logger.error(
                "RoutingEngine.send_intent: falhou após %.3fs - error=%s",
                latency,
                exc,
                exc_info=True,
            )
            raise



    def get_intent(self, intent_id: str) -> tuple[CommunicationIntentRecord, list] | None:
        """Retorna intent e seus deliveries."""
        intent = self.routing_store.get_intent(intent_id)
        if intent is None:
            return None
        deliveries = self.routing_store.get_deliveries(intent_id)
        return intent, deliveries

    def list_intents(self) -> list[CommunicationIntentRecord]:
        """Lista todas as intents."""
        return self.routing_store.list_intents()

    def cancel_intent(self, intent_id: str) -> CommunicationIntentRecord | None:
        """Cancela uma intent pendente."""
        from comunicacao.routing.models import IntentStatus
        intent = self.routing_store.get_intent(intent_id)
        if intent is None:
            return None
        if intent.status not in {IntentStatus.COMPLETED, IntentStatus.FAILED, IntentStatus.CANCELLED}:
            intent.status = IntentStatus.CANCELLED
            self.routing_store.save_intent(intent)
        return intent

    async def send_batch(self, intents: list[CommunicationIntentCreate]) -> tuple[list, list]:
        """Processa lista de intents em batch."""
        accepted = []
        rejected = []
        for intent_create in intents:
            try:
                result = await self.send_intent(intent_create)
                accepted.append(result)
            except Exception as exc:
                rejected.append({"error": str(exc)})
        return accepted, rejected

    def metrics(self) -> dict:
        """Retorna métricas do engine."""
        all_intents = self.routing_store.list_intents()
        by_channel: dict[str, int] = {}
        fallback_count = 0
        escalation_count = 0
        for intent in all_intents:
            for event in intent.timeline:
                if event.event_type == "dispatched":
                    ch = event.details.get("channel", "unknown")
                    by_channel[ch] = by_channel.get(ch, 0) + 1
                elif event.event_type in {"all_channels_failed", "fallback_activated"}:
                    fallback_count += 1
                elif event.event_type == "escalated":
                    escalation_count += 1
        return {
            "total_intents": len(all_intents),
            "by_channel": by_channel,
            "fallback_count": fallback_count,
            "escalation_count": escalation_count,
        }

    def list_rules(self) -> list:
        """Lista todas as regras de roteamento."""
        return self.rule_matcher.rule_store.list_rules()

    def upsert_rule(self, rule) -> any:
        """Salva ou atualiza regra de roteamento."""
        self.rule_matcher.rule_store.save_rule(rule)
        return rule

# Alias para compatibilidade com código existente
RoutingService = RoutingEngine
