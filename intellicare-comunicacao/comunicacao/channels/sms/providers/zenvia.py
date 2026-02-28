"""
Zenvia SMS Provider (D4).

Implementa provider SMS usando Zenvia API.
"""

import logging
from typing import Dict, Any, Optional

import httpx

from comunicacao.channels.sms.config import ZenviaConfig
from comunicacao.channels.sms.providers.base import BaseSMSProvider

logger = logging.getLogger(__name__)


class ZenviaSMSProvider(BaseSMSProvider):
    """Provider SMS usando Zenvia."""

    def __init__(self, config: ZenviaConfig):
        """
        Inicializa provider Zenvia.

        Args:
            config: Configuração Zenvia.
        """
        self._config = config
        self._base_url = "https://api.zenvia.com/v2"
        self._client = httpx.AsyncClient(
            headers={
                "X-API-TOKEN": config.api_token,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    @property
    def provider_name(self) -> str:
        """Nome do provider."""
        return "zenvia"

    async def send(self, to: str, text: str) -> Dict[str, Any]:
        """
        Envia SMS via Zenvia.

        Args:
            to: Número do destinatário.
            text: Texto da mensagem.

        Returns:
            Dict: Resposta com message_id.

        Raises:
            httpx.HTTPError: Se erro na API.
        """
        # Validar número
        if not self.validate_phone_number(to):
            raise ValueError(f"Número inválido: {to}")

        # Truncar mensagem se necessário
        text = self.truncate_message(text)

        # Enviar
        url = f"{self._base_url}/channels/sms/messages"
        payload = {
            "from": self._config.from_name,
            "to": to,
            "contents": [{"type": "text", "text": text}],
        }

        logger.info("Enviando SMS via Zenvia: to=%s", to)
        response = await self._client.post(url, json=payload)
        response.raise_for_status()

        result = response.json()
        logger.info("SMS enviado via Zenvia: id=%s", result["id"])

        return {
            "message_id": result["id"],
            "status": "sent",
            "to": to,
        }

    async def get_status(self, message_id: str) -> Optional[str]:
        """
        Consulta status de mensagem no Zenvia.

        Nota: Zenvia não tem endpoint de consulta. Status vem via webhook.

        Args:
            message_id: ID da mensagem.

        Returns:
            Optional[str]: None (não suportado).
        """
        logger.warning("Zenvia não suporta consulta de status via API: %s", message_id)
        return None

    async def health_check(self) -> bool:
        """
        Verifica saúde do Zenvia.

        Returns:
            bool: True se API está acessível.
        """
        try:
            # Testar endpoint de subscriptions (público)
            url = f"{self._base_url}/subscriptions"
            response = await self._client.get(url)
            response.raise_for_status()

            logger.info("Zenvia health check: OK")
            return True

        except Exception as exc:
            logger.error("Zenvia health check falhou: %s", exc)
            return False

    async def close(self):
        """Fecha cliente HTTP."""
        await self._client.aclose()

