"""Monitor de fallback e retry para o engine de roteamento - Fase 3."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from comunicacao.dispatchers.base import DispatcherManager, ResolvedRecipient
    from comunicacao.routing.models import CommunicationIntentRecord
    from comunicacao.storage.routing_repository import RoutingStore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetryConfig:
    """Configuração de retry para um canal."""
    
    max_attempts: int = 3
    initial_delay_seconds: int = 5
    max_delay_seconds: int = 300
    exponential_base: float = 2.0
    timeout_seconds: int = 30


@dataclass(slots=True)
class ChannelAttempt:
    """Registro de tentativa em um canal."""
    
    channel: str
    attempt_number: int
    started_at: datetime
    timeout_at: datetime
    completed: bool = False
    success: bool = False
    error_message: str | None = None


class FallbackMonitor:
    """
    Monitor de fallback e retry para o engine de roteamento.
    
    Responsabilidades:
    - Monitorar timeout de tentativas
    - Implementar retry com exponential backoff
    - Acionar próximo canal em caso de falha
    - Escalonar para coordinator quando todos os canais falharem
    """

    def __init__(
        self,
        routing_store: RoutingStore,
        dispatcher_manager: DispatcherManager,
        default_retry_config: RetryConfig | None = None,
    ) -> None:
        self.routing_store = routing_store
        self.dispatcher_manager = dispatcher_manager
        self.default_retry_config = default_retry_config or RetryConfig()
        
        # Mapa de tentativas ativas: intent_id -> list[ChannelAttempt]
        self._active_attempts: dict[UUID, list[ChannelAttempt]] = {}
        
        logger.info("FallbackMonitor inicializado")

    def calculate_retry_delay(self, attempt_number: int, config: RetryConfig) -> int:
        """
        Calcula delay para retry com exponential backoff.
        
        Fórmula: min(initial_delay * (base ^ attempt), max_delay)
        """
        delay = config.initial_delay_seconds * (config.exponential_base ** (attempt_number - 1))
        return min(int(delay), config.max_delay_seconds)

    def is_expired(self, intent: CommunicationIntentRecord) -> bool:
        """
        Verifica se intent expirou.

        Retorna True se expires_at foi definido e já passou.
        """
        if intent.expires_at is None:
            return False

        return datetime.now(UTC) >= intent.expires_at

    def should_retry(
        self,
        intent: CommunicationIntentRecord,
        channel: str,
        attempt_number: int,
    ) -> bool:
        """
        Verifica se deve fazer retry em um canal.

        Considera:
        - max_attempts da intent
        - Número de tentativas já feitas
        - expires_at da intent
        """
        # Verifica se excedeu max_attempts
        if attempt_number >= intent.max_attempts:
            logger.info(
                "Intent %s: max_attempts atingido (%d) para canal %s",
                intent.id,
                intent.max_attempts,
                channel,
            )
            return False

        # Verifica se intent expirou
        if self.is_expired(intent):
            logger.info(
                "Intent %s: expirado (expires_at=%s)",
                intent.id,
                intent.expires_at,
            )
            return False

        return True

    async def try_channel(
        self,
        intent: CommunicationIntentRecord,
        channel: str,
        attempt_number: int,
        resolved_recipient: ResolvedRecipient | None = None,
        config: RetryConfig | None = None,
    ) -> ChannelAttempt:
        """
        Tenta enviar mensagem em um canal.
        
        Retorna ChannelAttempt com resultado da tentativa.
        """
        config = config or self.default_retry_config
        
        started_at = datetime.now(UTC)
        timeout_at = started_at + timedelta(seconds=config.timeout_seconds)
        
        attempt = ChannelAttempt(
            channel=channel,
            attempt_number=attempt_number,
            started_at=started_at,
            timeout_at=timeout_at,
        )
        
        logger.info(
            "Intent %s: tentando canal %s (tentativa %d/%d)",
            intent.id,
            channel,
            attempt_number,
            intent.max_attempts,
        )
        
        try:
            # Envia mensagem com timeout
            dispatcher = self.dispatcher_manager.get_dispatcher(channel)

            if not dispatcher:
                raise ValueError(f"Dispatcher não encontrado para canal: {channel}")

            # Cria task de envio com timeout
            from comunicacao.dispatchers.base import ChannelMessage, RenderedContent

            message = ChannelMessage(
                intent_id=str(intent.id),
                correlation_id=intent.correlation_id,
                channel=channel,
                recipient=resolved_recipient or self._build_default_recipient(intent),
                content=RenderedContent(
                    format="plain",
                    body=intent.content_raw or "Conteúdo não disponível",
                ),
                metadata={
                    "severity": intent.severity,
                    "category": intent.category,
                },
            )

            # Executa com timeout
            try:
                result = await asyncio.wait_for(
                    dispatcher.send(message),
                    timeout=config.timeout_seconds,
                )

                attempt.completed = True
                attempt.success = result.success

                if not result.success:
                    attempt.error_message = result.error_message or "Unknown error"

                logger.info(
                    "Intent %s: canal %s %s (tentativa %d)",
                    intent.id,
                    channel,
                    "enviado com sucesso" if result.success else f"falhou: {attempt.error_message}",
                    attempt_number,
                )

            except asyncio.TimeoutError:
                attempt.completed = True
                attempt.success = False
                attempt.error_message = f"Timeout após {config.timeout_seconds}s"

                logger.warning(
                    "Intent %s: timeout no canal %s após %ds (tentativa %d)",
                    intent.id,
                    channel,
                    config.timeout_seconds,
                    attempt_number,
                )

        except Exception as e:
            attempt.completed = True
            attempt.success = False
            attempt.error_message = str(e)

            logger.error(
                "Intent %s: erro no canal %s (tentativa %d): %s",
                intent.id,
                channel,
                attempt_number,
                e,
            )

        return attempt

    async def try_with_retry(
        self,
        intent: CommunicationIntentRecord,
        channel: str,
        resolved_recipient: ResolvedRecipient | None = None,
        config: RetryConfig | None = None,
    ) -> bool:
        """
        Tenta enviar em um canal com retry automático.

        Retorna True se sucesso, False se todas as tentativas falharam.
        """
        config = config or self.default_retry_config

        for attempt_number in range(1, intent.max_attempts + 1):
            # Verifica se intent expirou antes de tentar
            if self.is_expired(intent):
                logger.warning(
                    "Intent %s: expirado antes da tentativa %d no canal %s",
                    intent.id,
                    attempt_number,
                    channel,
                )
                return False

            # Verifica se deve fazer retry (passa attempt anterior, não o atual)
            if attempt_number > 1:
                if not self.should_retry(intent, channel, attempt_number - 1):
                    return False

                # Aguarda delay antes de retry (baseado na tentativa anterior)
                delay = self.calculate_retry_delay(attempt_number - 1, config)
                logger.info(
                    "Intent %s: aguardando %ds antes de retry %d no canal %s",
                    intent.id,
                    delay,
                    attempt_number,
                    channel,
                )
                await asyncio.sleep(delay)

            # Tenta enviar
            attempt = await self.try_channel(
                intent=intent,
                channel=channel,
                attempt_number=attempt_number,
                resolved_recipient=resolved_recipient,
                config=config,
            )

            # Registra tentativa
            if intent.id not in self._active_attempts:
                self._active_attempts[intent.id] = []
            self._active_attempts[intent.id].append(attempt)

            # Se sucesso, retorna
            if attempt.success:
                return True

        # Todas as tentativas falharam
        logger.warning(
            "Intent %s: todas as %d tentativas falharam no canal %s",
            intent.id,
            intent.max_attempts,
            channel,
        )
        return False

    async def try_channel_sequence(
        self,
        intent: CommunicationIntentRecord,
        channels: list[str],
        resolved_recipient: ResolvedRecipient | None = None,
        config: RetryConfig | None = None,
    ) -> tuple[bool, str | None]:
        """
        Tenta enviar em uma sequência de canais com fallback automático.

        Retorna (sucesso, canal_usado).
        """
        config = config or self.default_retry_config

        for channel in channels:
            # Verifica se intent expirou antes de tentar próximo canal
            if self.is_expired(intent):
                logger.warning(
                    "Intent %s: expirado durante sequência de canais (canal atual: %s)",
                    intent.id,
                    channel,
                )
                return False, None

            logger.info(
                "Intent %s: tentando canal %s (sequência: %s)",
                intent.id,
                channel,
                channels,
            )

            success = await self.try_with_retry(
                intent=intent,
                channel=channel,
                resolved_recipient=resolved_recipient,
                config=config,
            )

            if success:
                logger.info(
                    "Intent %s: sucesso no canal %s",
                    intent.id,
                    channel,
                )
                return True, channel

        # Todos os canais falharam
        logger.error(
            "Intent %s: todos os canais falharam (sequência: %s)",
            intent.id,
            channels,
        )
        return False, None

    async def escalate(
        self,
        intent: CommunicationIntentRecord,
        reason: str,
    ) -> UUID | None:
        """
        Escala intent para coordinator criando nova intent com parent_intent_id.

        Retorna ID da intent de escalation ou None se falhar.
        """
        logger.warning(
            "Intent %s: escalando para coordinator - razão: %s",
            intent.id,
            reason,
        )

        try:
            from comunicacao.routing.models import (
                CommunicationIntentCreate,
                RecipientType,
            )

            # Coleta informações sobre as tentativas falhadas
            attempts = self.get_attempts(intent.id)
            failed_channels = list({attempt.channel for attempt in attempts if not attempt.success})
            total_attempts = len(attempts)

            # Determina severity da escalation
            # Se original era CRITICAL, mantém CRITICAL
            # Se era HIGH, mantém HIGH
            # Caso contrário, eleva para HIGH
            escalation_severity = intent.severity
            if intent.severity not in ["critical", "high"]:
                escalation_severity = "high"

            # Monta conteúdo da escalation
            escalation_content = self._build_escalation_content(
                intent=intent,
                reason=reason,
                failed_channels=failed_channels,
                total_attempts=total_attempts,
            )

            # Cria intent de escalation
            coordinator_id = "coordinator"
            if isinstance(intent.metadata, dict):
                coordinator_id = str(intent.metadata.get("coordinator_id") or coordinator_id)

            escalation_intent_create = CommunicationIntentCreate(
                source_module="intellicare-comunicacao",
                source_event_id=f"escalation_{intent.id}",
                recipient_type=RecipientType.COORDINATOR,
                recipient_id=coordinator_id,
                severity=escalation_severity,
                category="escalation",
                content_raw=escalation_content,
                correlation_id=intent.correlation_id,
                parent_intent_id=intent.id,
                max_attempts=3,
                metadata={
                    "escalation_reason": reason,
                    "original_intent_id": str(intent.id),
                    "original_severity": intent.severity,
                    "original_category": intent.category,
                    "failed_channels": failed_channels,
                    "total_attempts": total_attempts,
                },
            )

            # Salva intent de escalation
            from comunicacao.routing.models import CommunicationIntentRecord
            escalation_intent = CommunicationIntentRecord(
                **escalation_intent_create.model_dump(exclude_unset=True),
            )

            self.routing_store.save_intent(escalation_intent)

            logger.info(
                "Intent %s: escalation criada com ID %s (severity=%s, coordinator)",
                intent.id,
                escalation_intent.id,
                escalation_severity,
            )

            return escalation_intent.id

        except Exception as e:
            logger.error(
                "Intent %s: erro ao criar escalation - %s",
                intent.id,
                e,
                exc_info=True,
            )
            return None

    def _build_escalation_content(
        self,
        intent: CommunicationIntentRecord,
        reason: str,
        failed_channels: list[str],
        total_attempts: int,
    ) -> str:
        """
        Constrói conteúdo da mensagem de escalation.
        """
        content_parts = [
            "🚨 ESCALATION ALERT",
            "",
            f"Uma comunicação {intent.severity.upper()} falhou após {total_attempts} tentativas.",
            "",
            f"**Razão**: {reason}",
            f"**Intent Original**: {intent.id}",
            f"**Categoria**: {intent.category}",
            f"**Destinatário**: {intent.recipient_type.value} - {intent.recipient_id}",
            "",
            f"**Canais Tentados**: {', '.join(failed_channels) if failed_channels else 'nenhum'}",
            "",
            "**Conteúdo Original**:",
            intent.content_raw or "(template-based)",
            "",
            "⚠️ Ação necessária: Verificar status do destinatário e canais de comunicação.",
        ]

        return "\n".join(content_parts)

    def get_attempts(self, intent_id: UUID) -> list[ChannelAttempt]:
        """Retorna todas as tentativas de um intent."""
        return self._active_attempts.get(intent_id, [])

    def clear_attempts(self, intent_id: UUID) -> None:
        """Limpa tentativas de um intent."""
        if intent_id in self._active_attempts:
            del self._active_attempts[intent_id]

    @staticmethod
    def _build_default_recipient(intent: CommunicationIntentRecord) -> ResolvedRecipient:
        from comunicacao.dispatchers.base import ResolvedRecipient
        return ResolvedRecipient(
            recipient_id=intent.recipient_id,
            recipient_type=intent.recipient_type.value,
            channels={},
        )
