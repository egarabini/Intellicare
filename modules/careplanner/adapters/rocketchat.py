"""Adapter async para integracao com Rocket.Chat."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from typing import Any

import httpx

from ..config import CareplannerSettings

logger = logging.getLogger(__name__)


class RocketChatAdapter:
    """Cliente async com auth em memoria, rate limit e retry simples."""

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings
        self._user_id: str | None = None
        self._auth_token: str | None = None
        self._client: httpx.AsyncClient | None = None
        self._rate_limit_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.rocketchat_url.rstrip("/"),
                timeout=30.0,
            )
        return self._client

    async def _throttle(self) -> None:
        async with self._rate_limit_lock:
            rate = max(self._settings.rocketchat_max_requests_per_second, 1)
            interval = 1.0 / rate
            now = asyncio.get_running_loop().time()
            elapsed = now - self._last_request_at
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
            self._last_request_at = asyncio.get_running_loop().time()

    async def login_bot(self) -> None:
        client = await self._get_client()
        response = await client.post(
            "/api/v1/login",
            json={
                "user": self._settings.rocketchat_bot_username,
                "password": self._settings.rocketchat_bot_password,
            },
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data", {})
        self._user_id = data.get("userId")
        self._auth_token = data.get("authToken")
        if not self._user_id or not self._auth_token:
            raise httpx.HTTPError("Rocket.Chat login sem userId/authToken")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        allow_unauthenticated: bool = False,
    ) -> httpx.Response:
        client = await self._get_client()
        retries = max(self._settings.rocketchat_max_retries, 1)
        for attempt in range(1, retries + 1):
            if not allow_unauthenticated and (not self._user_id or not self._auth_token):
                await self.login_bot()
            headers = {}
            if not allow_unauthenticated:
                headers = {
                    "X-Auth-Token": self._auth_token or "",
                    "X-User-Id": self._user_id or "",
                }
            await self._throttle()
            response = await client.request(method, path, json=json, params=params, headers=headers)
            if response.status_code == 401 and not allow_unauthenticated:
                self._auth_token = None
                self._user_id = None
                if attempt < retries:
                    continue
            if response.status_code >= 500 and attempt < retries:
                await asyncio.sleep(0.2 * (2 ** (attempt - 1)))
                continue
            response.raise_for_status()
            return response
        raise httpx.HTTPError(f"Rocket.Chat request failed after {retries} attempts: {path}")

    async def ensure_room(self, tenant_slug: str, patient_ref: str) -> str:
        room_name = f"ic_{tenant_slug}_{patient_ref}"
        try:
            response = await self._request(
                "POST",
                "/api/v1/channels.create",
                json={"name": room_name},
            )
            room = response.json().get("channel", {})
            room_id = room.get("_id")
            if room_id:
                return room_id
        except httpx.HTTPStatusError as exc:
            body = exc.response.text.lower()
            if "already exists" not in body and exc.response.status_code != 400:
                raise

        response = await self._request(
            "GET",
            "/api/v1/channels.info",
            params={"roomName": room_name},
        )
        room = response.json().get("channel", {})
        room_id = room.get("_id")
        if not room_id:
            raise httpx.HTTPError("Rocket.Chat nao retornou room id")
        return room_id

    async def post_message(self, rc_room_id: str, text: str) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/api/v1/chat.postMessage",
            json={"roomId": rc_room_id, "text": text},
        )
        return response.json()

    async def archive_room(self, rc_room_id: str) -> None:
        await self._request(
            "POST",
            "/api/v1/channels.archive",
            json={"roomId": rc_room_id},
        )

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(
            self._settings.rocketchat_webhook_token.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        received = signature.removeprefix("sha256=")
        return hmac.compare_digest(expected, received)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
