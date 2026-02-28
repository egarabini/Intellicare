"""Handle /ajuda command — contextual help (EF-W012)."""

from __future__ import annotations

from typing import Any

from wanda.bot.models import BotCommand

_ALL_COMMANDS = [c.value for c in BotCommand]


async def handle_ajuda(formatter: Any) -> tuple[str, list[dict]]:
    attachments = formatter.help_text(_ALL_COMMANDS)
    return "Olá! Sou o assistente clínico IntelliCare. Comandos disponíveis:", attachments
