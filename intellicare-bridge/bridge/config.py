"""Configuração do intellicare-bridge (stub)."""
from __future__ import annotations

import os


def get_grahame_base_url() -> str:
    return os.environ.get("GRAHAME_BASE_URL", "http://localhost:8012")


def get_wanda_base_url() -> str:
    return os.environ.get("WANDA_BASE_URL", "http://localhost:8004")
