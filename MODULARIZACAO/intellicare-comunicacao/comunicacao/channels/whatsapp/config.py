"""
Configuração para WhatsApp Business API (D4).

Define classes de configuração para Meta Cloud API.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field


class WhatsAppConfig(BaseModel):
    """Configuração WhatsApp Business API."""

    # Meta Cloud API
    graph_api_version: str = "v18.0"
    graph_api_url: str = "https://graph.facebook.com"
    phone_number_id: str  # ID do número de telefone no Meta
    business_account_id: str  # WABA ID
    access_token: str  # Token de acesso permanente

    # Webhook (para receber status e mensagens)
    webhook_verify_token: str  # Token para verificação do webhook

    # Rate Limiting
    max_messages_per_second: int = 80  # WhatsApp Business tier limit

    # Templates
    default_language: str = "pt_BR"

    # Geral
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "WhatsAppConfig":
        """
        Carrega configuração de variáveis de ambiente.

        Returns:
            WhatsAppConfig: Configuração carregada.

        Raises:
            ValueError: Se variáveis obrigatórias não estiverem configuradas.
        """
        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        webhook_verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")

        if not all([phone_number_id, business_account_id, access_token, webhook_verify_token]):
            raise ValueError(
                "WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_BUSINESS_ACCOUNT_ID, "
                "WHATSAPP_ACCESS_TOKEN e WHATSAPP_WEBHOOK_VERIFY_TOKEN são obrigatórios"
            )

        return cls(
            graph_api_version=os.getenv("WHATSAPP_GRAPH_API_VERSION", "v18.0"),
            graph_api_url=os.getenv("WHATSAPP_GRAPH_API_URL", "https://graph.facebook.com"),
            phone_number_id=phone_number_id,
            business_account_id=business_account_id,
            access_token=access_token,
            webhook_verify_token=webhook_verify_token,
            max_messages_per_second=int(os.getenv("WHATSAPP_MAX_MESSAGES_PER_SECOND", "80")),
            default_language=os.getenv("WHATSAPP_DEFAULT_LANGUAGE", "pt_BR"),
            enabled=os.getenv("WHATSAPP_ENABLED", "true").lower() == "true",
            timeout_seconds=int(os.getenv("WHATSAPP_TIMEOUT", "30")),
            max_retries=int(os.getenv("WHATSAPP_MAX_RETRIES", "3")),
        )

    @property
    def base_url(self) -> str:
        """
        URL base da API.

        Returns:
            str: URL base.
        """
        return f"{self.graph_api_url}/{self.graph_api_version}"

    @property
    def messages_url(self) -> str:
        """
        URL para envio de mensagens.

        Returns:
            str: URL de mensagens.
        """
        return f"{self.base_url}/{self.phone_number_id}/messages"

    class Config:
        """Pydantic config."""

        from_attributes = True

