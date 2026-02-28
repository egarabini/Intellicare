"""
FCM Push Service (D4).

Implementa envio de Push via Firebase Cloud Messaging v1 API.
"""

import json
import logging
from typing import Dict, Optional

import aiohttp
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from comunicacao.channels.models import PushSubscription
from comunicacao.channels.push.config import FCMConfig
from comunicacao.channels.push.models import PushPayload

logger = logging.getLogger(__name__)


class FCMPushService:
    """Envia Push via Firebase Cloud Messaging v1 API."""

    def __init__(self, config: FCMConfig):
        """
        Inicializa serviço FCM.

        Args:
            config: Configuração FCM.
        """
        self._config = config
        self._credentials: Optional[service_account.Credentials] = None
        self._session: Optional[aiohttp.ClientSession] = None

    def _get_access_token(self) -> str:
        """
        Obtém access token do Google OAuth2.

        Returns:
            str: Access token.

        Raises:
            Exception: Se falhar ao obter token.
        """
        if not self._credentials:
            # Carregar service account
            self._credentials = service_account.Credentials.from_service_account_file(
                self._config.service_account_key_path,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"],
            )

        # Refresh token se necessário
        if not self._credentials.valid:
            self._credentials.refresh(Request())

        return self._credentials.token

    async def send(self, subscription: PushSubscription, payload: PushPayload) -> bool:
        """
        Envia via FCM HTTP v1 API.

        POST https://fcm.googleapis.com/v1/projects/{project_id}/messages:send
        Authorization: Bearer {access_token}
        Body: {
            "message": {
                "token": subscription.fcm_token,
                "notification": {
                    "title": payload.title,
                    "body": payload.body,
                    "image": payload.icon
                },
                "data": payload.data,
                "android": { "priority": "high" },
                "webpush": { "headers": { "Urgency": "high" } }
            }
        }

        Args:
            subscription: Subscription do dispositivo.
            payload: Payload da notificação.

        Returns:
            bool: True se enviado com sucesso, False caso contrário.
        """
        if not subscription.fcm_token:
            logger.error("Subscription FCM sem token: %s", subscription.id)
            return False

        try:
            # Obter access token
            access_token = self._get_access_token()

            # Montar payload FCM
            fcm_payload = {
                "message": {
                    "token": subscription.fcm_token,
                    "notification": {
                        "title": payload.title,
                        "body": payload.body,
                    },
                    "android": {"priority": "high"},
                    "webpush": {"headers": {"Urgency": "high"}},
                }
            }

            # Adicionar icon se presente
            if payload.icon:
                fcm_payload["message"]["notification"]["image"] = payload.icon

            # Adicionar data se presente
            if payload.data:
                fcm_payload["message"]["data"] = {k: str(v) for k, v in payload.data.items()}

            # Enviar via HTTP
            url = f"https://fcm.googleapis.com/v1/projects/{self._config.project_id}/messages:send"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            if not self._session:
                self._session = aiohttp.ClientSession()

            async with self._session.post(url, json=fcm_payload, headers=headers) as response:
                if response.status == 200:
                    logger.info("Push FCM enviado com sucesso: subscription=%s", subscription.id)
                    return True

                # Token inválido
                if response.status == 404:
                    logger.warning("Token FCM inválido (404): %s", subscription.id)
                    return False

                error_text = await response.text()
                logger.error("Erro ao enviar push FCM: %s - %s", response.status, error_text)
                return False

        except Exception as exc:
            logger.error("Erro inesperado ao enviar push FCM: %s - %s", subscription.id, exc)
            return False

    async def send_to_topic(self, topic: str, payload: PushPayload) -> bool:
        """
        Envia para topic (ex: todos os médicos).

        Args:
            topic: Nome do topic.
            payload: Payload da notificação.

        Returns:
            bool: True se enviado com sucesso.
        """
        try:
            access_token = self._get_access_token()

            fcm_payload = {
                "message": {
                    "topic": topic,
                    "notification": {
                        "title": payload.title,
                        "body": payload.body,
                    },
                    "android": {"priority": "high"},
                }
            }

            url = f"https://fcm.googleapis.com/v1/projects/{self._config.project_id}/messages:send"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            if not self._session:
                self._session = aiohttp.ClientSession()

            async with self._session.post(url, json=fcm_payload, headers=headers) as response:
                return response.status == 200

        except Exception as exc:
            logger.error("Erro ao enviar push FCM para topic %s: %s", topic, exc)
            return False

    async def health_check(self) -> bool:
        """
        Verifica saúde do serviço FCM.

        Returns:
            bool: True se configurado e acessível.
        """
        try:
            # Tentar obter access token
            self._get_access_token()
            return True
        except Exception as exc:
            logger.error("FCM health check falhou: %s", exc)
            return False

    async def close(self) -> None:
        """Fecha sessão HTTP."""
        if self._session:
            await self._session.close()
            self._session = None

