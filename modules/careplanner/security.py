"""Utilitarios de seguranca e LGPD para o CarePlanner."""
from __future__ import annotations


def mask_phone(phone: str | None) -> str:
    if not phone:
        return ""
    return phone[:6] + "****" + phone[-4:] if len(phone) > 9 else "***"


def mask_content(content: str | None, max_chars: int = 20) -> str:
    if not content:
        return ""
    safe = content[:max_chars]
    return f"{safe}[…]" if len(content) > max_chars else safe


def mask_jwt(token: str | None) -> str:
    if not token:
        return ""
    parts = token.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1][:8]}…"
    return token[:12] + "…"
