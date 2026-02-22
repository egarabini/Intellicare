"""Handle /teleconsulta command — create Jitsi room via Comunicacao (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def handle_teleconsulta(
    patient_id: str,
    http_client: Optional[Any],
    module_urls: dict[str, str],
    user_name: str,
    formatter: Any,
) -> tuple[str, list[dict]]:
    """Return (text, attachments) for the /teleconsulta command."""
    if not patient_id:
        return "Informe o ID do paciente: `/teleconsulta <id>`", []

    room_url: Optional[str] = None
    comunicacao_url = module_urls.get("intellicare-comunicacao", "")

    if comunicacao_url and http_client:
        try:
            resp = await http_client.post(
                f"{comunicacao_url}/api/v1/teleconsulta/create",
                json={"patient_id": patient_id, "created_by": user_name},
                timeout=10.0,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                room_url = data.get("room_url") or data.get("url")
        except Exception as exc:
            logger.warning("Teleconsulta creation failed: %s", exc)

    if room_url:
        text = f"Sala de teleconsulta criada para `{patient_id}`:"
        attachments = [{
            "color": "#2ea44f",
            "title": "Teleconsulta Jitsi",
            "title_link": room_url,
            "text": f"[Entrar na sala]({room_url})",
        }]
    else:
        text = f"Teleconsulta indisponível para `{patient_id}`."
        attachments = formatter.error("Módulo Comunicacao não acessível.")

    return text, attachments
