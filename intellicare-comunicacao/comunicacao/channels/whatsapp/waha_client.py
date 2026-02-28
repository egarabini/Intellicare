"""Cliente HTTP para WAHA (WhatsApp HTTP API)."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class WAHAClient:
    """Cliente HTTP para envio de mensagens via WAHA."""

    def __init__(
        self,
        *,
        base_url: str,
        session: str = "default",
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        if not base_url:
            raise ValueError("WAHA base_url é obrigatório")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-Api-Key"] = api_key
        self._base_url = base_url.rstrip("/")
        self._session = session
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
        )

    @staticmethod
    def _to_chat_id(phone: str) -> str:
        """Converte número em formato E.164 para chatId WAHA."""
        digits = re.sub(r"\D", "", phone or "")
        if not digits:
            raise ValueError("Número de telefone inválido")
        return f"{digits}@c.us"

    async def send_text(self, *, to: str, text: str) -> dict[str, Any]:
        """Envia texto via WAHA."""
        if not text or not text.strip():
            raise ValueError("Texto da mensagem não pode ser vazio")
        payload = {
            "session": self._session,
            "chatId": self._to_chat_id(to),
            "text": text,
        }
        try:
            response = await self._client.post(f"{self._base_url}/api/sendText", json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info("WAHA send_text enviado: chat_id=%s", payload["chatId"])
            return data
        except httpx.TimeoutException:
            logger.error("Timeout ao enviar mensagem via WAHA")
            raise
        except httpx.HTTPStatusError as exc:
            logger.error("WAHA retornou erro HTTP: status=%s", exc.response.status_code)
            raise

    async def health_check(self) -> dict[str, Any]:
        """Verifica disponibilidade da sessão WAHA."""
        try:
            response = await self._client.get(f"{self._base_url}/api/sessions/{self._session}")
            response.raise_for_status()
            data = response.json()
            status = str(data.get("status", "")).upper()
            available = status in {"WORKING", "STARTED", "CONNECTED"}
            return {
                "available": available,
                "session": self._session,
                "status": status or "UNKNOWN",
                "raw": data,
            }
        except Exception as exc:
            logger.warning("WAHA indisponível no health_check: %s", exc)
            return {
                "available": False,
                "session": self._session,
                "status": "UNAVAILABLE",
                "error": str(exc),
            }

    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        await self._client.aclose()
