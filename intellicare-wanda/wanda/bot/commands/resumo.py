"""Handle /resumo command — follow-up report from Geralda (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def handle_resumo(
    patient_id: str,
    http_client: Optional[Any],
    module_urls: dict[str, str],
    formatter: Any,
) -> tuple[str, list[dict]]:
    """Return (text, attachments) for the /resumo command."""
    if not patient_id:
        return "Informe o ID do paciente: `/resumo <id>`", []

    report = "Relatório não disponível."
    geralda_url = module_urls.get("intellicare-geralda", "")

    if geralda_url and http_client:
        try:
            resp = await http_client.get(
                f"{geralda_url}/api/v1/patients/{patient_id}/followup-report",
                timeout=15.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                report = data.get("report") or data.get("summary") or report
        except Exception as exc:
            logger.warning("Geralda follow-up report failed: %s", exc)
            report = f"Erro ao consultar Geralda: {exc}"

    attachments = formatter.followup_report(report)
    return f"Relatório de acompanhamento — paciente `{patient_id}`:", attachments
