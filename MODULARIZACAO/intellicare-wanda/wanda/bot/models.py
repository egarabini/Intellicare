"""Domain models for the Rocket.Chat bot (EF-W012)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class BotCommand(str, Enum):
    PACIENTE = "paciente"
    GUIDELINE = "guideline"
    RESUMO = "resumo"
    ALERTA = "alerta"
    TELECONSULTA = "teleconsulta"
    AJUDA = "ajuda"
    STATUS = "status"


@dataclass
class RCIncomingMessage:
    """Raw payload received from Rocket.Chat webhook."""

    token: str
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    text: str
    trigger_word: str = "@intellicare"


@dataclass
class ParsedCommand:
    """Result of parsing a Rocket.Chat message into a bot command."""

    command: Optional[BotCommand]
    args: list[str] = field(default_factory=list)
    patient_id: Optional[str] = None
    raw_text: str = ""
    is_valid: bool = True
    error: Optional[str] = None


@dataclass
class AuthResult:
    """Result of authorizing a user to execute a command."""

    authorized: bool
    user_roles: list[str] = field(default_factory=list)
    reason: Optional[str] = None


@dataclass
class RCMessage:
    """A message to send back to Rocket.Chat."""

    channel: str
    text: str
    attachments: list[dict] = field(default_factory=list)
    alias: str = "IntelliCare"
    emoji: str = ":robot:"
