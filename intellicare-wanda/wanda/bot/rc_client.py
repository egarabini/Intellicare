"""Rocket.Chat HTTP client for sending bot messages (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from wanda.bot.models import RCMessage

logger = logging.getLogger(__name__)

_POST_MESSAGE_PATH = "/api/v1/chat.postMessage"


class RocketChatBotClient:
    """Sends messages to Rocket.Chat via REST API.

    Falls back to log-only when no HTTP client or URL is configured.
    """

    def __init__(
        self,
        base_url: str = "",
        bot_user_id: str = "",
        bot_token: str = "",
        http_client: Optional[Any] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._user_id = bot_user_id
        self._token = bot_token
        self._http = http_client
        self._enabled = bool(base_url and bot_token and http_client)

    async def send(self, message: RCMessage) -> bool:
        """Send a message to Rocket.Chat. Returns True on success."""
        if not self._enabled:
            logger.info(
                "[RC-Bot dry-run] channel=%s text=%s",
                message.channel, message.text[:80],
            )
            return True

        payload: dict[str, Any] = {
            "channel": message.channel,
            "text": message.text,
            "alias": message.alias,
            "emoji": message.emoji,
        }
        if message.attachments:
            payload["attachments"] = message.attachments

        try:
            resp = await self._http.post(
                f"{self._base_url}{_POST_MESSAGE_PATH}",
                json=payload,
                headers={
                    "X-Auth-Token": self._token,
                    "X-User-Id": self._user_id,
                },
                timeout=10.0,
            )
            if resp.status_code < 300:
                return True
            logger.error("RC send failed: %d %s", resp.status_code, resp.text[:200])
            return False
        except Exception as exc:
            logger.error("RC send exception: %s", exc)
            return False

    async def send_text(self, channel: str, text: str) -> bool:
        return await self.send(RCMessage(channel=channel, text=text))
