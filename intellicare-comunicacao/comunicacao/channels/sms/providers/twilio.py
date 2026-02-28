"""
Twilio SMS Provider (D4).

Implementa provider SMS usando Twilio API.
"""

import logging
from typing import Dict, Any, Optional

import httpx

from comunicacao.channels.sms.config import TwilioConfig
from comunicacao.channels.sms.providers.base import BaseSMSProvider

logger = logging.getLogger(__name__)


class TwilioSMSProvider(BaseSMSProvider):
    """Provider SMS usando Twilio."""

    def __init__(self, config: TwilioConfig):
        """
        Inicializa provider Twilio.

        Args:
            config: Configuração Twilio.
        """
        self._config = config
        self._base_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.account_sid}"
        self._client = httpx.AsyncClient(
            auth=(config.account_sid, config.auth_token),
            timeout=30.0,
        )

    @property
    def provider_name(self) -> str:
        """Nome do provider."""
        return "twilio"

    async def send(self, to: str, text: str) -> Dict[str, Any]:
        """
        Envia SMS via Twilio.

        Args:
            to: Número do destinatário.
            text: Texto da mensagem.

        Returns:
            Dict: Resposta com message_id (SID).

        Raises:
            httpx.HTTPError: Se erro na API.
        """
        # Validar número
        if not self.validate_phone_number(to):
            raise ValueError(f"Número inválido: {to}")

        # Truncar mensagem se necessário
        text = self.truncate_message(text)

        # Enviar
        url = f"{self._base_url}/Messages.json"
        data = {
            "From": self._config.from_number,
            "To": to,
            "Body": text,
        }

        logger.info("Enviando SMS via Twilio: to=%s", to)
        response = await self._client.post(url, data=data)
        response.raise_for_status()

        result = response.json()
        logger.info("SMS enviado via Twilio: sid=%s", result["sid"])

        return {
            "message_id": result["sid"],
            "status": result["status"],
            "to": result["to"],
        }

    async def get_status(self, message_id: str) -> Optional[str]:
        """
        Consulta status de mensagem no Twilio.

        Args:
            message_id: SID da mensagem.

        Returns:
            Optional[str]: Status da mensagem.
        """
        try:
            url = f"{self._base_url}/Messages/{message_id}.json"
            response = await self._client.get(url)
            response.raise_for_status()

            result = response.json()
            status = result["status"]

            # Mapear status Twilio -> padrão
            status_map = {
                "queued": "pending",
                "sending": "sent",
                "sent": "sent",
                "delivered": "delivered",
                "failed": "failed",
                "undelivered": "failed",
            }

            return status_map.get(status, "unknown")

        except Exception as exc:
            logger.error("Erro ao consultar status Twilio: %s", exc)
            return None

    async def health_check(self) -> bool:
        """
        Verifica saúde do Twilio.

        Returns:
            bool: True se API está acessível.
        """
        try:
            # Testar endpoint de account
            url = f"{self._base_url}.json"
            response = await self._client.get(url)
            response.raise_for_status()

            logger.info("Twilio health check: OK")
            return True

        except Exception as exc:
            logger.error("Twilio health check falhou: %s", exc)
            return False

    async def close(self):
        """Fecha cliente HTTP."""
        await self._client.aclose()

