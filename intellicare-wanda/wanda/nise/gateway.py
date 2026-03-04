"""DrNiseGateway — full pipeline: session → IPS → FLOWISE → filter → audit (EF-W013)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from wanda.nise.audit_logger import NiseAuditLogger
from wanda.nise.flowise_client import FlowiseClient
from wanda.nise.ips_simplifier import IPSSimplifier
from wanda.nise.models import DrNiseResponse, PatientMessage
from wanda.nise.response_filter import NiseResponseFilter
from wanda.nise.session_manager import NiseSessionManager

logger = logging.getLogger(__name__)

_FALLBACK_MESSAGE = (
    "Olá! Estou temporariamente indisponível. "
    "Para assistência médica urgente, contate sua equipe de saúde."
)


class DrNiseGateway:
    """Orchestrates the Dr. Nise patient chatbot pipeline.

    Pipeline:
      1. Get or create session
      2. Fetch simplified IPS (minimum privilege)
      3. Send to FLOWISE with session history
      4. Filter response (safety check)
      5. Log audit trail
      6. Escalate if needed
      7. Return DrNiseResponse
    """

    def __init__(
        self,
        flowise_client: Optional[FlowiseClient] = None,
        session_manager: Optional[NiseSessionManager] = None,
        audit_logger: Optional[NiseAuditLogger] = None,
        alert_hub: Optional[Any] = None,
        ips_loader: Optional[Any] = None,  # callable(patient_id) → dict
        fallback_message: str = _FALLBACK_MESSAGE,
        escalation_enabled: bool = True,
    ) -> None:
        self._flowise = flowise_client or FlowiseClient()
        self._sessions = session_manager or NiseSessionManager()
        self._audit = audit_logger or NiseAuditLogger()
        self._alert_hub = alert_hub
        self._ips_loader = ips_loader
        self._filter = NiseResponseFilter()
        self._simplifier = IPSSimplifier()
        self._fallback = fallback_message
        self._escalation_enabled = escalation_enabled

    async def chat(self, message: PatientMessage) -> DrNiseResponse:
        """Process a patient message and return Dr. Nise's response."""

        # 1. Session
        session = await self._sessions.get_or_create(
            tenant_id=message.tenant_id,
            patient_id=message.patient_id,
            session_id=message.session_id,
            channel=message.channel,
        )

        # 2. Log patient message
        await self._audit.log(session.session_id, "patient", message.content)
        await self._sessions.append_message(session, "patient", message.content)

        # 3. Load simplified IPS as context override
        override_config: dict = {}
        if self._ips_loader is not None:
            try:
                ips = await self._ips_loader(message.patient_id)
                simplified = self._simplifier.simplify(ips)
                override_config["vars"] = {"patient_context": simplified}
            except Exception as exc:
                logger.warning("IPS load failed for Nise: %s", exc)

        # 4. Call FLOWISE
        # Limit history to last N messages (trim to pairs to keep coherence)
        history = session.history[:-1]  # exclude the message we just added

        flowise_resp = await self._flowise.predict(
            question=message.content,
            history=history,
            override_config=override_config or None,
        )

        if not flowise_resp.success or not flowise_resp.text:
            response_text = self._fallback
            flagged = False
            escalate = False
        else:
            # 5. Filter
            filter_result = self._filter.filter(flowise_resp.text)
            response_text = filter_result.filtered_text
            flagged = not filter_result.safe
            escalate = filter_result.requires_escalation

        # 6. Update session with response
        await self._sessions.append_message(session, "nise", response_text)
        if flagged:
            await self._sessions.flag_message(session)
        await self._audit.log(session.session_id, "nise", response_text, flagged=flagged)

        # 7. Escalation
        if escalate and self._escalation_enabled and self._alert_hub is not None:
            await self._trigger_escalation(session.session_id, message.patient_id)
            await self._sessions.escalate(session)

        return DrNiseResponse(
            session_id=session.session_id,
            text=response_text,
            flagged=flagged,
            escalated=escalate,
            message_count=session.message_count,
        )

    async def end_session(self, tenant_id: str, session_id: str, patient_id: str) -> bool:
        session = await self._sessions.get_or_create(
            tenant_id=tenant_id, patient_id=patient_id, session_id=session_id
        )
        await self._sessions.end_session(session)
        return True

    async def _trigger_escalation(self, session_id: str, patient_id: str) -> None:
        """Create a critical alert via AlertHub when escalation keyword detected."""
        from wanda.alerts.models import ClinicalAlert  # noqa: PLC0415

        alert = ClinicalAlert(
            patient_id=patient_id,
            source_agent="intellicare-nise",
            alert_type="condition_worsened",
            severity="critical",
            title="Dr. Nise: possível emergência detectada",
            description=f"Palavra-chave de emergência detectada na sessão {session_id}",
            recommended_action="Contatar paciente imediatamente.",
            clinical_data={"session_id": session_id, "source": "nise_filter"},
        )
        try:
            await self._alert_hub.receive_alert(alert)
        except Exception as exc:
            logger.error("Nise escalation alert failed: %s", exc)

    async def flowise_health(self) -> bool:
        return await self._flowise.health_check()
