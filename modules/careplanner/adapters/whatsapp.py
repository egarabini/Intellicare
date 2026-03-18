"""Adapter async para integracao com WhatsApp via Evolution API."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import CareplannerSettings

logger = logging.getLogger(__name__)


class WhatsAppAdapter:
    """Cliente async para Evolution API — envia/recebe via WhatsApp."""

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.evolution_api_url.rstrip("/"),
                headers={"apikey": self._settings.evolution_api_key},
                timeout=30.0,
            )
        return self._client

    def _normalize_phone(self, phone_e164: str) -> str:
        """Remove + e retorna apenas dígitos. Ex: +5511999999999 → 5511999999999"""
        return phone_e164.lstrip("+")

    async def send_message(self, phone_e164: str, text: str) -> dict[str, Any]:
        """Envia mensagem de texto para o número E.164 via Evolution API."""
        client = await self._get_client()
        instance = self._settings.evolution_instance_name
        phone = self._normalize_phone(phone_e164)

        for attempt in range(1, self._settings.evolution_max_retries + 1):
            try:
                response = await client.post(
                    f"/message/sendText/{instance}",
                    json={
                        "number": phone,
                        "textMessage": {"text": text},
                    },
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt < self._settings.evolution_max_retries:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                raise
        raise httpx.HTTPError(f"Evolution API falhou após {self._settings.evolution_max_retries} tentativas")

    def extract_phone_from_jid(self, remote_jid: str) -> str:
        """Extrai número de telefone do JID do WhatsApp.
        Ex: '5511999999999@s.whatsapp.net' → '5511999999999'
        """
        return remote_jid.split("@")[0]

    def verify_webhook_secret(self, token: str) -> bool:
        """Verifica token simples no path do webhook."""
        secret = self._settings.evolution_webhook_secret
        if not secret:
            return True   # sem configuração, aceita (dev/staging sem segredo)
        return token == secret

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
