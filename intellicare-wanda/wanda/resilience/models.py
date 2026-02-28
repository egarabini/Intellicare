"""Modelos de resiliencia."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitSnapshot:
    agent_name: str
    state: CircuitState
    failures: int
    successes: int
