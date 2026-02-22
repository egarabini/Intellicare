"""
Push Dispatcher (D4).

Implementa ChannelDispatcher para Push Notifications (VAPID/FCM).
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.models import PushSubscription, ExternalMessageLog, ExternalMessageStatus, ExternalMessageDirection
from comunicacao.channels.push.config import PushConfig
from comunicacao.channels.push.fcm_service import FCMPushService
from comunicacao.channels.push.models import PushPayload
from comunicacao.channels.push.vapid_service import VAPIDPushService
from comunicacao.dispatchers.base import (
    ChannelMessage,
    DispatchResult,
    DeliveryStatus,
    ChannelHealth,
    ChannelCapabilities,
    ResolvedRecipient,
    RecipientValidation,
)

logger = logging.getLogger(__name__)


class PushDispatcher:
    """Dispatcher para Push Notifications (VAPID + FCM)."""

    def __init__(self, db: AsyncSession, config: PushConfig):
        """
        Inicializa dispatcher.

        Args:
            db: Sessão do banco de dados.
            config: Configuração de push.
        """
        self._db = db
        self._config = config
        self._vapid = VAPIDPushService(config.vapid)
        self._fcm = FCMPushService(config.fcm) if config.fcm else None
        self.channel = "push"

    async def send(self, message: ChannelMessage) -> DispatchResult:
        """
        Envia push notification.

        Lógica:
        1. Buscar subscriptions do usuário (pode ter várias: desktop, mobile)
        2. Para cada subscription:
           a. Se subscription.type == "web" → VAPID
           b. Se subscription.type == "fcm" → FCM
        3. Enviar em paralelo para todas as subscriptions
        4. Retornar resultado consolidado

        Args:
            message: Mensagem a enviar.

        Returns:
            DispatchResult: Resultado do envio.
        """
        try:
            # Buscar subscriptions ativas do usuário
            stmt = select(PushSubscription).where(
                PushSubscription.user_id == message.recipient.recipient_id,
                PushSubscription.active == True,  # noqa: E712
            )
            result = await self._db.execute(stmt)
            subscriptions = result.scalars().all()

            if not subscriptions:
                logger.warning("Nenhuma subscription ativa para user_id=%s", message.recipient.recipient_id)
                return DispatchResult(
                    success=False,
                    error_code="no_subscriptions",
                    error_message="Usuário não possui subscriptions ativas",
                    timestamp=datetime.now(UTC),
                )

            # Criar payload
            payload = PushPayload(
                title=message.content.subject or "IntelliCare",
                body=message.content.body[:200],  # Truncar para push
                data=message.metadata,
                require_interaction=message.metadata.get("severity") == "CRITICAL",
                silent=message.metadata.get("severity") == "LOW",
            )

            # Enviar para todas as subscriptions
            sent_count = 0
            failed_count = 0
            channel_message_ids = []

            for subscription in subscriptions:
                success = False

                if subscription.subscription_type == "web":
                    success = await self._vapid.send(subscription, payload)
                elif subscription.subscription_type == "fcm" and self._fcm:
                    success = await self._fcm.send(subscription, payload)

                if success:
                    sent_count += 1
                    # Logar mensagem enviada
                    log_entry = ExternalMessageLog(
                        channel="push",
                        direction=ExternalMessageDirection.OUTBOUND,
                        recipient_id=message.recipient.recipient_id,
                        recipient_address=subscription.device_name or subscription.subscription_type,
                        template_name=message.metadata.get("template_name"),
                        message_summary=payload.body[:500],
                        status=ExternalMessageStatus.SENT,
                        sent_at=datetime.now(UTC),
                    )
                    channel_message_ids.append(str(log_entry.id))
                else:
                    failed_count += 1

            if sent_count > 0:
                return DispatchResult(
                    success=True,
                    channel_message_id=channel_message_ids[0] if channel_message_ids else None,
                    timestamp=datetime.now(UTC),
                    metadata={"sent_to": sent_count, "failed": failed_count},
                )

            return DispatchResult(
                success=False,
                error_code="all_failed",
                error_message=f"Falha ao enviar para todas as {len(subscriptions)} subscriptions",
                timestamp=datetime.now(UTC),
            )

        except Exception as exc:
            logger.error("Erro ao enviar push: %s", exc, exc_info=True)
            return DispatchResult(
                success=False,
                error_code="internal_error",
                error_message=str(exc),
                timestamp=datetime.now(UTC),
            )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        """
        Push não tem read receipt nativo. Retorna DELIVERED se enviado sem erro.

        Args:
            channel_message_id: ID da mensagem.

        Returns:
            DeliveryStatus: Status de entrega.
        """
        # Push não tem tracking de entrega nativo
        return DeliveryStatus.DELIVERED

    async def cancel(self, channel_message_id: str) -> bool:
        """
        Push não suporta cancelamento após envio.

        Args:
            channel_message_id: ID da mensagem.

        Returns:
            bool: Sempre False (não suportado).
        """
        logger.warning("Push não suporta cancelamento: %s", channel_message_id)
        return False

    async def health_check(self) -> ChannelHealth:
        """
        Verifica saúde do canal push.

        Returns:
            ChannelHealth: Status de saúde.
        """
        vapid_ok = await self._vapid.health_check()
        fcm_ok = await self._fcm.health_check() if self._fcm else True

        available = vapid_ok and fcm_ok

        details = {
            "vapid": "ok" if vapid_ok else "error",
            "fcm": "ok" if fcm_ok else "error" if self._fcm else "disabled",
        }

        return ChannelHealth(
            channel=self.channel,
            available=available,
            status="healthy" if available else "degraded",
            details=details,
        )

    async def test_send(self, recipient: ResolvedRecipient) -> DispatchResult:
        """
        Envia mensagem de teste.

        Args:
            recipient: Destinatário.

        Returns:
            DispatchResult: Resultado do envio.
        """
        from comunicacao.dispatchers.base import RenderedContent

        message = ChannelMessage(
            intent_id="test-intent",
            correlation_id=f"test-{uuid4()}",
            channel=self.channel,
            recipient=recipient,
            content=RenderedContent(
                format="json",
                body="Esta é uma notificação de teste do IntelliCare.",
                subject="Teste IntelliCare",
            ),
            metadata={"test": True},
        )

        return await self.send(message)

    async def get_capabilities(self) -> ChannelCapabilities:
        """
        Retorna capacidades do canal.

        Returns:
            ChannelCapabilities: Capacidades.
        """
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=False,
            supports_rich_content=True,  # Suporta icon, badge, actions
            supports_attachments=False,
            supports_interactive=True,  # Suporta actions/botões
            max_message_length=200,  # Limite típico de push
            metadata={
                "format": "json",
                "vapid_enabled": True,
                "fcm_enabled": self._fcm is not None,
            },
        )

    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation:
        """
        Valida se destinatário é válido para push.

        Args:
            recipient: Destinatário a validar.

        Returns:
            RecipientValidation: Resultado da validação.
        """
        # Verificar se usuário tem subscriptions ativas
        stmt = select(PushSubscription).where(
            PushSubscription.user_id == recipient.recipient_id,
            PushSubscription.active == True,  # noqa: E712
        )
        result = await self._db.execute(stmt)
        subscriptions = result.scalars().all()

        if not subscriptions:
            return RecipientValidation(
                valid=False,
                reason="Usuário não possui subscriptions ativas de push",
            )

        return RecipientValidation(
            valid=True,
            metadata={"subscription_count": len(subscriptions)},
        )

