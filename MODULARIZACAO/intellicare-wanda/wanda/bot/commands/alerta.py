"""Handle /alerta command — create manual critical alert via AlertHub (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def handle_alerta(
    patient_id: str,
    description: str,
    user_name: str,
    alert_hub: Optional[Any],
    formatter: Any,
) -> tuple[str, list[dict]]:
    """Return (text, attachments) for the /alerta command."""
    if not patient_id:
        return "Informe o ID do paciente: `/alerta <id> <descricao>`", []
    if not description:
        return "Informe a descrição: `/alerta <id> <descricao>`", []
    if alert_hub is None:
        return "AlertHub não disponível.", formatter.error("AlertHub desabilitado.")

    from wanda.alerts.models import ClinicalAlert  # noqa: PLC0415

    alert = ClinicalAlert(
        patient_id=patient_id,
        source_agent=f"bot:{user_name}",
        alert_type="condition_worsened",
        severity="critical",
        title=f"Alerta manual: {description[:80]}",
        description=description,
        recommended_action="Verificar paciente imediatamente.",
        clinical_data={"triggered_by": user_name, "source": "rc_bot"},
    )
    result = await alert_hub.receive_alert(alert)

    attachments = formatter.alert_created(result.alert_id, "critical", result.priority_score)
    return f"Alerta crítico criado para `{patient_id}`:", attachments
