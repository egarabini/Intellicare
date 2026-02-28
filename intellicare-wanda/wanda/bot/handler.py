"""Main bot handler — entry point for Rocket.Chat webhooks (EF-W012)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from wanda.bot.auth import BotAuthMiddleware
from wanda.bot.context_store import BotContextStore
from wanda.bot.models import BotCommand, RCIncomingMessage, RCMessage
from wanda.bot.parser import CommandParser
from wanda.bot.rc_client import RocketChatBotClient
from wanda.bot.router import CommandRouter

logger = logging.getLogger(__name__)


class WandaBotHandler:
    """Processes incoming Rocket.Chat webhook payloads.

    Pipeline:
      1. Validate webhook token
      2. Filter self-messages (prevent echo loops)
      3. Parse command
      4. Load context
      5. Authorize
      6. Route to handler
      7. Send response
      8. Update context
    """

    def __init__(
        self,
        webhook_token: str = "",
        bot_user_id: str = "",
        rc_client: Optional[RocketChatBotClient] = None,
        router: Optional[CommandRouter] = None,
        auth: Optional[BotAuthMiddleware] = None,
        context_store: Optional[BotContextStore] = None,
    ) -> None:
        self._webhook_token = webhook_token
        self._bot_user_id = bot_user_id
        self._rc_client = rc_client or RocketChatBotClient()
        self._router = router or CommandRouter()
        self._auth = auth or BotAuthMiddleware()
        self._context = context_store or BotContextStore()
        self._parser = CommandParser()
        self._command_log: list[dict[str, Any]] = []

    async def handle_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Process a raw webhook payload from Rocket.Chat."""
        token = payload.get("token", "")
        if self._webhook_token and token != self._webhook_token:
            logger.warning("Invalid webhook token received")
            return {"status": "unauthorized"}

        msg = RCIncomingMessage(
            token=token,
            channel_id=payload.get("channel_id", ""),
            channel_name=payload.get("channel_name", ""),
            user_id=payload.get("user_id", ""),
            user_name=payload.get("user_name", ""),
            text=payload.get("text", ""),
            trigger_word=payload.get("trigger_word", "@intellicare"),
        )

        # Filter self-messages
        if msg.user_id == self._bot_user_id:
            return {"status": "ignored", "reason": "self-message"}

        # Load context (last patient_id etc.)
        ctx = await self._context.get(msg.user_id, msg.channel_id)
        context_patient_id = ctx.get("patient_id")

        # Parse command
        parsed = self._parser.parse(msg.text, context_patient_id)
        if not parsed.is_valid or parsed.command is None:
            if parsed.error and parsed.error != "sem trigger":
                await self._rc_client.send_text(msg.channel_name, f"❓ {parsed.error}. Use `/ajuda`.")
            return {"status": "ignored", "reason": parsed.error or "no trigger"}

        # Authorize
        auth_result = await self._auth.authorize(
            parsed.command,
            msg.user_id,
            rc_token=payload.get("user_token"),
        )
        if not auth_result.authorized:
            await self._rc_client.send_text(
                msg.channel_name,
                f"🚫 Sem permissão para `/{parsed.command.value}`. {auth_result.reason or ''}",
            )
            return {"status": "unauthorized", "command": parsed.command.value}

        # Route
        try:
            text, attachments = await self._router.route(parsed, msg.user_name)
        except Exception as exc:
            logger.exception("Command routing error: %s", exc)
            text = "Erro interno ao processar o comando."
            attachments = []

        # Send response
        response = RCMessage(
            channel=msg.channel_name,
            text=text,
            attachments=attachments,
        )
        await self._rc_client.send(response)

        # Update context
        if parsed.patient_id:
            await self._context.update(msg.user_id, msg.channel_id, {"patient_id": parsed.patient_id})

        # Log
        self._command_log.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "user": msg.user_name,
            "command": parsed.command.value if parsed.command else "unknown",
            "patient_id": parsed.patient_id,
        })
        if len(self._command_log) > 500:
            self._command_log = self._command_log[-200:]

        return {"status": "ok", "command": parsed.command.value}

    @property
    def recent_commands(self) -> list[dict[str, Any]]:
        return list(reversed(self._command_log[-50:]))

    @property
    def metrics(self) -> dict[str, Any]:
        from collections import Counter  # noqa: PLC0415
        counts = Counter(e["command"] for e in self._command_log)
        return {"total": len(self._command_log), "by_command": dict(counts)}
