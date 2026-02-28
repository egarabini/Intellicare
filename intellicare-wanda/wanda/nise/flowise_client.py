"""FLOWISE HTTP client for Dr. Nise (EF-W013)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from wanda.nise.models import FlowiseResponse

logger = logging.getLogger(__name__)


class FlowiseClient:
    """Sends chat messages to the FLOWISE prediction API.

    POST /api/v1/prediction/{chatflow_id}
    Body: {"question": "...", "history": [...], "overrideConfig": {...}}
    """

    def __init__(
        self,
        base_url: str = "",
        chatflow_id: str = "",
        api_key: str = "",
        http_client: Optional[Any] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._chatflow_id = chatflow_id
        self._api_key = api_key
        self._http = http_client
        self._timeout = timeout_seconds
        self._enabled = bool(base_url and chatflow_id and http_client)

    async def predict(
        self,
        question: str,
        history: Optional[list[dict]] = None,
        override_config: Optional[dict] = None,
    ) -> FlowiseResponse:
        if not self._enabled:
            logger.debug("FlowiseClient not configured — returning fallback")
            return FlowiseResponse(
                text="",
                success=False,
                error="FLOWISE nao configurado",
            )

        payload: dict[str, Any] = {"question": question}
        if history:
            payload["history"] = history
        if override_config:
            payload["overrideConfig"] = override_config

        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            resp = await self._http.post(
                f"{self._base_url}/api/v1/prediction/{self._chatflow_id}",
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            # FLOWISE returns {"text": "..."} or {"answer": "..."} depending on version
            text = data.get("text") or data.get("answer") or str(data)
            return FlowiseResponse(text=text, success=True)
        except Exception as exc:
            logger.error("FlowiseClient.predict failed: %s", exc)
            return FlowiseResponse(text="", success=False, error=str(exc))

    async def health_check(self) -> bool:
        if not self._http or not self._base_url:
            return False
        try:
            resp = await self._http.get(f"{self._base_url}/api/v1/chatflows", timeout=5.0)
            return resp.status_code < 300
        except Exception:
            return False
