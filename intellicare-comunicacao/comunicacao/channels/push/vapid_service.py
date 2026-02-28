"""
VAPID Push Service (D4).

Implementa envio de Web Push via protocolo VAPID (RFC 8292).
"""

import json
import logging
from typing import Dict, Optional

import aiohttp
from pywebpush import webpush, WebPushException

from comunicacao.channels.models import PushSubscription
from comunicacao.channels.push.config import VAPIDConfig
from comunicacao.channels.push.models import PushPayload

logger = logging.getLogger(__name__)


class VAPIDPushService:
    """Envia Web Push via protocolo VAPID (RFC 8292)."""

    def __init__(self, config: VAPIDConfig):
        """
        Inicializa serviço VAPID.

        Args:
            config: Configuração VAPID.
        """
        self._config = config

    async def send(self, subscription: PushSubscription, payload: PushPayload) -> bool:
        """
        Envia push via VAPID.

        Fluxo:
        1. Serializar payload como JSON
        2. Criptografar com chaves do subscription (p256dh, auth)
        3. Assinar com VAPID private key
        4. POST para subscription.endpoint
        5. Se 201 → sucesso
        6. Se 410 (Gone) → marcar subscription como inativa
        7. Se 429 → retry com backoff

        Args:
            subscription: Subscription do dispositivo.
            payload: Payload da notificação.

        Returns:
            bool: True se enviado com sucesso, False caso contrário.
        """
        if not subscription.endpoint or not subscription.p256dh_key or not subscription.auth_key:
            logger.error("Subscription VAPID incompleta: %s", subscription.id)
            return False

        try:
            # Serializar payload
            payload_json = json.dumps(payload.model_dump())

            # Preparar subscription info para pywebpush
            subscription_info = {
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh_key,
                    "auth": subscription.auth_key,
                },
            }

            # Enviar via pywebpush (síncrono, mas rápido)
            # TODO: Considerar implementação async pura se necessário
            webpush(
                subscription_info=subscription_info,
                data=payload_json,
                vapid_private_key=self._config.private_key,
                vapid_claims={
                    "sub": self._config.subject,
                },
                ttl=self._config.ttl,
            )

            logger.info("Push VAPID enviado com sucesso: subscription=%s", subscription.id)
            return True

        except WebPushException as exc:
            # 410 Gone = subscription expirada
            if exc.response and exc.response.status_code == 410:
                logger.warning("Subscription VAPID expirada (410 Gone): %s", subscription.id)
                # Caller deve marcar como inativa
                return False

            # 429 Too Many Requests = rate limit
            if exc.response and exc.response.status_code == 429:
                logger.warning("Rate limit VAPID (429): %s", subscription.id)
                return False

            logger.error("Erro ao enviar push VAPID: %s - %s", subscription.id, exc)
            return False

        except Exception as exc:
            logger.error("Erro inesperado ao enviar push VAPID: %s - %s", subscription.id, exc)
            return False

    async def health_check(self) -> bool:
        """
        Verifica saúde do serviço VAPID.

        Returns:
            bool: True se configurado corretamente.
        """
        # VAPID está OK se chaves estão configuradas
        return bool(self._config.private_key and self._config.public_key)

