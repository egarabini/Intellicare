"""
WhatsApp Client para Meta Graph API (D4).

Cliente HTTP para enviar mensagens via WhatsApp Business API.
"""

import logging
from typing import Dict, List, Optional, Any

import httpx

from comunicacao.channels.whatsapp.config import WhatsAppConfig
from comunicacao.channels.whatsapp.templates import get_template

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Cliente para WhatsApp Business API (Meta Cloud API)."""

    def __init__(self, config: WhatsAppConfig):
        """
        Inicializa cliente WhatsApp.

        Args:
            config: Configuração WhatsApp.
        """
        self._config = config
        self._client = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            headers={
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json",
            },
        )

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        params: List[str],
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Envia mensagem usando template pré-aprovado.

        Args:
            to: Número do destinatário (+55...).
            template_name: Nome do template.
            params: Parâmetros do template.
            language: Código do idioma (default: pt_BR).

        Returns:
            Dict: Resposta da API com message_id.

        Raises:
            httpx.HTTPError: Se erro na API.
        """
        # Obter template
        template = get_template(template_name)
        lang = language or self._config.default_language

        # Construir payload
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template["meta_template_name"],
                "language": {"code": lang},
                "components": self._build_template_components(template, params),
            },
        }

        # Enviar
        logger.info("Enviando template WhatsApp: to=%s, template=%s", to, template_name)
        response = await self._client.post(self._config.messages_url, json=payload)
        response.raise_for_status()

        result = response.json()
        logger.info("Template enviado: message_id=%s", result["messages"][0]["id"])

        return result

    async def send_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto (session message - janela 24h).

        Args:
            to: Número do destinatário.
            text: Texto da mensagem.

        Returns:
            Dict: Resposta da API.

        Raises:
            httpx.HTTPError: Se erro na API.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        logger.info("Enviando texto WhatsApp: to=%s", to)
        response = await self._client.post(self._config.messages_url, json=payload)
        response.raise_for_status()

        result = response.json()
        logger.info("Texto enviado: message_id=%s", result["messages"][0]["id"])

        return result

    async def get_message_status(self, message_id: str) -> Optional[str]:
        """
        Consulta status de mensagem.

        Nota: WhatsApp não tem endpoint de consulta. Status vem via webhook.

        Args:
            message_id: ID da mensagem.

        Returns:
            Optional[str]: None (não suportado).
        """
        logger.warning("WhatsApp não suporta consulta de status via API: %s", message_id)
        return None

    async def health_check(self) -> bool:
        """
        Verifica conectividade com Meta Graph API.

        Returns:
            bool: True se API está acessível.
        """
        try:
            # Testar endpoint de business profile
            url = f"{self._config.base_url}/{self._config.phone_number_id}"
            response = await self._client.get(url, params={"fields": "id,verified_name"})
            response.raise_for_status()

            logger.info("WhatsApp API health check: OK")
            return True

        except Exception as exc:
            logger.error("WhatsApp API health check falhou: %s", exc)
            return False

    def _build_template_components(
        self, template: Dict[str, Any], params: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Constrói componentes do template com parâmetros.

        Args:
            template: Template.
            params: Parâmetros.

        Returns:
            List[Dict]: Componentes formatados.
        """
        components = []

        # Encontrar componente BODY
        for component in template["components"]:
            if component["type"] == "BODY":
                # Construir parâmetros
                parameters = [{"type": "text", "text": param} for param in params]

                components.append(
                    {
                        "type": "body",
                        "parameters": parameters,
                    }
                )
                break

        return components

    async def close(self):
        """Fecha cliente HTTP."""
        await self._client.aclose()

