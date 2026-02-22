"""Handle /paciente command — patient summary from IPS + alerts (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def handle_paciente(
    patient_id: str,
    http_client: Optional[Any],
    module_urls: dict[str, str],
    alert_hub: Optional[Any],
    formatter: Any,
) -> tuple[str, list[dict]]:
    """Return (text, attachments) for the /paciente command."""
    if not patient_id:
        return "Informe o ID do paciente: `/paciente <id>`", []

    ips: Optional[dict] = None
    plan: Optional[str] = None

    # Fetch IPS from Florence
    florence_url = module_urls.get("intellicare-florence", "")
    if florence_url and http_client:
        try:
            resp = await http_client.get(
                f"{florence_url}/api/v1/ips/{patient_id}", timeout=10.0
            )
            if resp.status_code == 200:
                ips = resp.json()
        except Exception as exc:
            logger.warning("Florence IPS fetch failed: %s", exc)

    # Fetch care plan from Geralda
    geralda_url = module_urls.get("intellicare-geralda", "")
    if geralda_url and http_client:
        try:
            resp = await http_client.get(
                f"{geralda_url}/api/v1/patients/{patient_id}/plan", timeout=10.0
            )
            if resp.status_code == 200:
                plan_data = resp.json()
                plan = plan_data.get("summary") or plan_data.get("plan")
        except Exception as exc:
            logger.warning("Geralda care plan fetch failed: %s", exc)

    # Pending alerts from AlertHub
    alerts: list[dict] = []
    if alert_hub:
        alerts = alert_hub.get_pending_alerts(limit=5, patient_id=patient_id)

    attachments = formatter.patient_summary(patient_id, ips, alerts, plan)
    return f"Resumo clínico para paciente `{patient_id}`:", attachments
