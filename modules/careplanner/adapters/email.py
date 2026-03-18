"""Adapter async para e-mail transacional via Listmonk."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import CareplannerSettings

logger = logging.getLogger(__name__)


class EmailAdapter:
    """Cliente async para Listmonk — envia e-mail transacional."""

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.listmonk_url.rstrip("/"),
                auth=(self._settings.listmonk_username, self._settings.listmonk_password),
                timeout=15.0,
            )
        return self._client

    async def send_message(self, email: str, subject: str, text: str) -> dict[str, Any]:
        """Envia e-mail transacional via Listmonk /api/tx."""
        client = await self._get_client()
        for attempt in range(1, 4):
            try:
                response = await client.post(
                    "/api/tx",
                    json={
                        "subscriber_email": email,
                        "template_id": 1,          # template padrão do Listmonk
                        "data": {
                            "subject": subject,
                            "body": text,
                            "from_email": self._settings.listmonk_sender_email,
                        },
                    },
                )
                response.raise_for_status()
                payload = response.json()
                return {"ok": True, "tx_id": payload.get("data", {}).get("id")}
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt < 3:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                return {"ok": False, "error": f"HTTP {exc.response.status_code}: {exc.response.text}"}
            except Exception as exc:
                if attempt < 3:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                return {"ok": False, "error": str(exc)}
        return {"ok": False, "error": "Listmonk falhou após 3 tentativas"}

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
