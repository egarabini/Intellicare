"""Command router — maps BotCommand to handler functions (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from wanda.bot.models import BotCommand, ParsedCommand

logger = logging.getLogger(__name__)


class CommandRouter:
    """Dispatches parsed commands to their handler functions.

    All external dependencies (HTTP, AlertHub, formatter, module URLs) are
    injected at construction time.
    """

    def __init__(
        self,
        http_client: Optional[Any] = None,
        alert_hub: Optional[Any] = None,
        module_urls: Optional[dict[str, str]] = None,
        formatter: Optional[Any] = None,
    ) -> None:
        from wanda.bot.formatter import RocketChatResponseFormatter  # noqa: PLC0415

        self._http = http_client
        self._alert_hub = alert_hub
        self._module_urls: dict[str, str] = module_urls or {}
        self._formatter = formatter or RocketChatResponseFormatter()

    async def route(
        self, parsed: ParsedCommand, user_name: str
    ) -> tuple[str, list[dict]]:
        """Dispatch to the appropriate handler. Returns (text, attachments)."""
        cmd = parsed.command
        patient_id = parsed.patient_id or ""
        args = parsed.args

        if cmd == BotCommand.PACIENTE:
            from wanda.bot.commands.paciente import handle_paciente  # noqa: PLC0415
            return await handle_paciente(patient_id, self._http, self._module_urls, self._alert_hub, self._formatter)

        if cmd == BotCommand.GUIDELINE:
            from wanda.bot.commands.guideline import handle_guideline  # noqa: PLC0415
            query = " ".join(args) if args else ""
            return await handle_guideline(query, self._http, self._module_urls, self._formatter)

        if cmd == BotCommand.RESUMO:
            from wanda.bot.commands.resumo import handle_resumo  # noqa: PLC0415
            return await handle_resumo(patient_id, self._http, self._module_urls, self._formatter)

        if cmd == BotCommand.ALERTA:
            from wanda.bot.commands.alerta import handle_alerta  # noqa: PLC0415
            description = " ".join(args)
            return await handle_alerta(patient_id, description, user_name, self._alert_hub, self._formatter)

        if cmd == BotCommand.TELECONSULTA:
            from wanda.bot.commands.teleconsulta import handle_teleconsulta  # noqa: PLC0415
            return await handle_teleconsulta(patient_id, self._http, self._module_urls, user_name, self._formatter)

        if cmd == BotCommand.STATUS:
            from wanda.bot.commands.status import handle_status  # noqa: PLC0415
            return await handle_status(self._http, self._module_urls, self._formatter)

        # Default: /ajuda
        from wanda.bot.commands.ajuda import handle_ajuda  # noqa: PLC0415
        return await handle_ajuda(self._formatter)

    def update_module_urls(self, urls: dict[str, str]) -> None:
        self._module_urls = urls
