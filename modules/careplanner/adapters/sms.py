"""Adapter async para SMS via Jasmin HTTP API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from ..config import CareplannerSettings

logger = logging.getLogger(__name__)


class SMSAdapter:
    """Cliente async para Jasmin — envia SMS via HTTP API."""

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.jasmin_url.rstrip("/"),
                timeout=15.0,
            )
        return self._client

    def _normalize_phone(self, phone_e164: str) -> str:
        """Remove + para formato internacional. Ex: +5511999 -> 5511999"""
        return phone_e164.lstrip("+")

    async def send_message(self, phone_e164: str, text: str) -> dict[str, Any]:
        """Envia SMS via Jasmin /send endpoint."""
        client = await self._get_client()
        phone = self._normalize_phone(phone_e164)

        # SMS: max 160 chars. Truncar com aviso no log se necessario.
        if len(text) > 160:
            logger.warning("SMS truncado de %d para 160 chars", len(text))
            text = text[:157] + "..."

        params = {
            "username": self._settings.jasmin_username,
            "password": self._settings.jasmin_password,
            "to": phone,
            "from": self._settings.jasmin_sender_id,
            "content": text,
        }

        for attempt in range(1, 4):
            try:
                response = await client.get("/send", params=params)
                response.raise_for_status()
                body = response.text.strip()
                if body.startswith("Error"):
                    raise httpx.HTTPError(f"Jasmin recusou SMS: {body}")
                return {"status": "sent", "jasmin_response": body}
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt < 3:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                raise
        raise httpx.HTTPError("Jasmin falhou apos 3 tentativas")

    def verify_webhook_secret(self, token: str) -> bool:
        """Jasmin nao assina webhooks — usar token simples no path."""
        secret = self._settings.jasmin_webhook_secret
        if not secret:
            return True
        return token == secret

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
