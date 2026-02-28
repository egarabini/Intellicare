"""Serviço de conformidade LGPD."""

from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import (
    CommunicationPreference,
    LegalBasis,
    LGPDDecision,
)

if TYPE_CHECKING:
    from comunicacao.routing.models import CommunicationIntentRecord


class LGPDComplianceService:
    """
    Serviço de conformidade LGPD.
    
    Verifica se uma comunicação pode ser enviada com base em:
    - Consentimento do paciente
    - Quiet hours (horários silenciosos)
    - Base legal (Art. 7º LGPD)
    - Overrides para alertas CRITICAL/HIGH
    """
    
    def __init__(self, db: AsyncSession, config: LGPDConfig):
        self._db = db
        self._config = config
    
    async def check_compliance(
        self,
        intent: CommunicationIntentRecord,
        channel: str,
    ) -> LGPDDecision:
        """
        Verifica conformidade LGPD para uma comunicação.
        
        Args:
            intent: Intenção de comunicação
            channel: Canal de comunicação (rocketchat, email, sms, etc.)
        
        Returns:
            LGPDDecision com allowed, reason, legal_basis, override_applied
        """
        # 1. Buscar preferências do paciente
        preferences = await self._get_preferences(intent.recipient_id)
        
        # 2. Verificar se é alerta CRITICAL (sempre permitido)
        if self._is_critical_alert(intent):
            return LGPDDecision(
                allowed=True,
                reason="Alerta CRITICAL permitido por base legal (Art. 7º, VII LGPD - tutela da saúde)",
                legal_basis=LegalBasis.HEALTH_PROTECTION,
                override_applied=True,
            )
        
        # 3. Verificar se é alerta HIGH (permitido com base legal)
        if self._is_high_alert(intent):
            return LGPDDecision(
                allowed=True,
                reason="Alerta HIGH permitido por base legal (Art. 11, II, f LGPD - proteção da vida)",
                legal_basis=LegalBasis.VITAL_PROTECTION,
                override_applied=True,
            )
        
        # 4. Verificar consentimento
        if not preferences or not preferences.consent_given:
            if self._config.block_without_consent:
                return LGPDDecision(
                    allowed=False,
                    reason="Paciente sem consentimento para comunicações",
                    legal_basis=None,
                    override_applied=False,
                )
        
        # 5. Verificar se consentimento expirou
        if preferences and preferences.consent_expires_at:
            if datetime.now() > preferences.consent_expires_at:
                return LGPDDecision(
                    allowed=False,
                    reason="Consentimento expirado - renovação necessária",
                    legal_basis=None,
                    override_applied=False,
                )
        
        # 6. Verificar opt-out do canal
        if not self._is_channel_enabled(preferences, channel):
            return LGPDDecision(
                allowed=False,
                reason=f"Paciente optou por não receber comunicações via {channel}",
                legal_basis=None,
                override_applied=False,
            )
        
        # 7. Verificar quiet hours
        quiet_hours_result = self._check_quiet_hours(preferences)
        if not quiet_hours_result["allowed"]:
            return LGPDDecision(
                allowed=False,
                reason=quiet_hours_result["reason"],
                legal_basis=LegalBasis.CONSENT,
                override_applied=False,
                deferred_until=quiet_hours_result.get("deferred_until"),
            )
        
        # 8. Tudo OK - permitido com base em consentimento
        return LGPDDecision(
            allowed=True,
            reason="Comunicação permitida com base em consentimento do paciente",
            legal_basis=LegalBasis.CONSENT,
            override_applied=False,
        )
    
    async def _get_preferences(self, patient_id: str) -> Optional[CommunicationPreference]:
        """Busca preferências do paciente no banco."""
        stmt = select(CommunicationPreference).where(
            CommunicationPreference.patient_id == patient_id
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
    
    def _is_critical_alert(self, intent: CommunicationIntentRecord) -> bool:
        """Verifica se é alerta CRITICAL."""
        if not self._config.critical_override_enabled:
            return False
        return intent.severity.strip().lower() == "critical"
    
    def _is_high_alert(self, intent: CommunicationIntentRecord) -> bool:
        """Verifica se é alerta HIGH."""
        if not self._config.high_alert_override_enabled:
            return False
        
        severity = intent.severity.strip().lower()
        category = intent.category.strip().lower()
        
        return severity == "high" and category in {"clinical_alert", "escalation"}
    
    def _is_channel_enabled(
        self,
        preferences: Optional[CommunicationPreference],
        channel: str,
    ) -> bool:
        """Verifica se canal está habilitado nas preferências."""
        if not preferences:
            return True  # Se não tem preferências, assume habilitado
        
        channel_map = {
            "rocketchat": preferences.rocketchat_enabled,
            "email": preferences.email_enabled,
            "sms": preferences.sms_enabled,
            "whatsapp": preferences.whatsapp_enabled,
            "push": preferences.push_enabled,
            "jitsi": preferences.jitsi_enabled,
        }
        
        return channel_map.get(channel, True)

    def _check_quiet_hours(
        self,
        preferences: Optional[CommunicationPreference],
    ) -> dict:
        """
        Verifica se está em horário silencioso (quiet hours).

        Returns:
            dict com allowed, reason, deferred_until
        """
        now = datetime.now()
        current_time = now.time()

        # Obter quiet hours (preferências do paciente ou padrão)
        if preferences and preferences.quiet_hours:
            quiet_start = self._parse_time(preferences.quiet_hours.get("start", self._config.default_quiet_hours_start))
            quiet_end = self._parse_time(preferences.quiet_hours.get("end", self._config.default_quiet_hours_end))
        else:
            quiet_start = self._parse_time(self._config.default_quiet_hours_start)
            quiet_end = self._parse_time(self._config.default_quiet_hours_end)

        # Verificar se está em quiet hours
        in_quiet_hours = self._is_in_time_range(current_time, quiet_start, quiet_end)

        if in_quiet_hours:
            # Calcular quando pode enviar (após quiet_end)
            deferred_until = datetime.combine(now.date(), quiet_end)
            if deferred_until <= now:
                # Se quiet_end já passou hoje, agendar para amanhã
                from datetime import timedelta
                deferred_until = deferred_until + timedelta(days=1)

            return {
                "allowed": False,
                "reason": f"Horário silencioso (quiet hours: {quiet_start.strftime('%H:%M')} - {quiet_end.strftime('%H:%M')})",
                "deferred_until": deferred_until,
            }

        return {
            "allowed": True,
            "reason": "Fora do horário silencioso",
        }

    def _parse_time(self, time_str: str) -> time:
        """Parse string HH:MM para time object."""
        hour, minute = map(int, time_str.split(":"))
        return time(hour=hour, minute=minute)

    def _is_in_time_range(self, current: time, start: time, end: time) -> bool:
        """
        Verifica se current está entre start e end.

        Lida com ranges que cruzam meia-noite (ex: 22:00 - 07:00).
        """
        if start <= end:
            # Range normal (ex: 08:00 - 18:00)
            return start <= current <= end
        else:
            # Range cruza meia-noite (ex: 22:00 - 07:00)
            return current >= start or current <= end

    def determine_legal_basis(
        self,
        intent: CommunicationIntentRecord,
        preferences: Optional[CommunicationPreference],
    ) -> Optional[LegalBasis]:
        """
        Determina a base legal para processamento de dados.

        Args:
            intent: Intenção de comunicação
            preferences: Preferências do paciente

        Returns:
            LegalBasis ou None
        """
        # CRITICAL: tutela da saúde
        if self._is_critical_alert(intent):
            return LegalBasis.HEALTH_PROTECTION

        # HIGH: proteção da vida
        if self._is_high_alert(intent):
            return LegalBasis.VITAL_PROTECTION

        # Com consentimento: consent
        if preferences and preferences.consent_given:
            return LegalBasis.CONSENT

        # SUS: interesse público
        if intent.source_module in {"oswaldo", "florence", "wanda"}:
            return LegalBasis.PUBLIC_INTEREST

        return None

