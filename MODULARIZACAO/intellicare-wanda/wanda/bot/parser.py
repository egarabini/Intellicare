"""Command parser — extracts bot commands from Rocket.Chat messages (EF-W012)."""

from __future__ import annotations

import re
from typing import Optional

from wanda.bot.models import BotCommand, ParsedCommand

_TRIGGER_PATTERNS = [r"@intellicare", r"^intellicare"]
_COMMAND_RE = re.compile(r"/(\w+)(.*)", re.DOTALL)
_PATIENT_ID_RE = re.compile(r"\b([A-Za-z0-9\-]{5,64})\b")

# Maps CLI command text → BotCommand enum
_COMMAND_MAP: dict[str, BotCommand] = {
    "paciente": BotCommand.PACIENTE,
    "guideline": BotCommand.GUIDELINE,
    "resumo": BotCommand.RESUMO,
    "alerta": BotCommand.ALERTA,
    "teleconsulta": BotCommand.TELECONSULTA,
    "ajuda": BotCommand.AJUDA,
    "ajuda-me": BotCommand.AJUDA,
    "help": BotCommand.AJUDA,
    "status": BotCommand.STATUS,
}


class CommandParser:
    """Parses Rocket.Chat message text into a ParsedCommand.

    Supported syntax:
        @intellicare /paciente <patient_id>
        @intellicare /alerta <patient_id> <description>
        @intellicare /ajuda
    """

    def parse(self, text: str, context_patient_id: Optional[str] = None) -> ParsedCommand:
        """Return ParsedCommand. command=None if text is not a bot command."""
        cleaned = text.strip()

        # Check for trigger word
        if not self._has_trigger(cleaned):
            return ParsedCommand(command=None, raw_text=text, is_valid=False, error="sem trigger")

        # Remove trigger word
        for pat in _TRIGGER_PATTERNS:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

        # Match /command [args]
        m = _COMMAND_RE.search(cleaned)
        if not m:
            return ParsedCommand(
                command=BotCommand.AJUDA,
                raw_text=text,
                is_valid=True,
            )

        cmd_text = m.group(1).lower()
        remainder = m.group(2).strip()
        args = remainder.split() if remainder else []

        command = _COMMAND_MAP.get(cmd_text)
        if command is None:
            return ParsedCommand(
                command=None,
                raw_text=text,
                is_valid=False,
                error=f"Comando desconhecido: /{cmd_text}",
            )

        # Extract patient_id from first arg or context
        patient_id: Optional[str] = None
        if args and _PATIENT_ID_RE.match(args[0]):
            patient_id = args[0]
            args = args[1:]
        elif context_patient_id:
            patient_id = context_patient_id

        return ParsedCommand(
            command=command,
            args=args,
            patient_id=patient_id,
            raw_text=text,
            is_valid=True,
        )

    @staticmethod
    def _has_trigger(text: str) -> bool:
        lower = text.lower()
        return any(re.search(pat, lower) for pat in _TRIGGER_PATTERNS)
