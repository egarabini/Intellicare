"""Serviço de gerenciamento de preferências de comunicação."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import (
    CommunicationPreference,
    ConsentLogEntry,
    ConsentStatus,
)


class PreferencesService:
    """
    Serviço de gerenciamento de preferências de comunicação.
    
    Responsável por CRUD de preferências do paciente:
    - Opt-in/opt-out por canal
    - Quiet hours
    - Consentimento
    """
    
    def __init__(self, db: AsyncSession, config: LGPDConfig):
        self._db = db
        self._config = config
    
    async def get_preferences(self, patient_id: str) -> Optional[CommunicationPreference]:
        """
        Busca preferências do paciente.
        
        Args:
            patient_id: ID do paciente
        
        Returns:
            CommunicationPreference ou None se não existir
        """
        stmt = select(CommunicationPreference).where(
            CommunicationPreference.patient_id == patient_id
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_default_preferences(self, patient_id: str) -> CommunicationPreference:
        """
        Cria preferências padrão para um paciente.
        
        Args:
            patient_id: ID do paciente
        
        Returns:
            CommunicationPreference criado
        """
        preferences = CommunicationPreference(
            patient_id=patient_id,
            rocketchat_enabled=True,
            email_enabled=True,
            sms_enabled=True,
            whatsapp_enabled=True,
            push_enabled=True,
            jitsi_enabled=True,
            quiet_hours={
                "start": self._config.default_quiet_hours_start,
                "end": self._config.default_quiet_hours_end,
            },
            consent_given=False,
        )
        
        self._db.add(preferences)
        await self._db.commit()
        await self._db.refresh(preferences)
        
        return preferences
    
    async def update_preferences(
        self,
        patient_id: str,
        rocketchat_enabled: Optional[bool] = None,
        email_enabled: Optional[bool] = None,
        sms_enabled: Optional[bool] = None,
        whatsapp_enabled: Optional[bool] = None,
        push_enabled: Optional[bool] = None,
        jitsi_enabled: Optional[bool] = None,
    ) -> CommunicationPreference:
        """
        Atualiza preferências de canais do paciente.
        
        Args:
            patient_id: ID do paciente
            *_enabled: Flags de habilitação por canal (None = não alterar)
        
        Returns:
            CommunicationPreference atualizado
        """
        preferences = await self.get_preferences(patient_id)
        
        if not preferences:
            preferences = await self.create_default_preferences(patient_id)
        
        # Atualizar apenas campos fornecidos
        if rocketchat_enabled is not None:
            preferences.rocketchat_enabled = rocketchat_enabled
        if email_enabled is not None:
            preferences.email_enabled = email_enabled
        if sms_enabled is not None:
            preferences.sms_enabled = sms_enabled
        if whatsapp_enabled is not None:
            preferences.whatsapp_enabled = whatsapp_enabled
        if push_enabled is not None:
            preferences.push_enabled = push_enabled
        if jitsi_enabled is not None:
            preferences.jitsi_enabled = jitsi_enabled
        
        await self._db.commit()
        await self._db.refresh(preferences)
        
        return preferences
    
    async def set_quiet_hours(
        self,
        patient_id: str,
        start: str,
        end: str,
    ) -> CommunicationPreference:
        """
        Configura horários silenciosos do paciente.
        
        Args:
            patient_id: ID do paciente
            start: Horário de início (HH:MM)
            end: Horário de fim (HH:MM)
        
        Returns:
            CommunicationPreference atualizado
        """
        preferences = await self.get_preferences(patient_id)
        
        if not preferences:
            preferences = await self.create_default_preferences(patient_id)
        
        preferences.quiet_hours = {
            "start": start,
            "end": end,
        }

        await self._db.commit()
        await self._db.refresh(preferences)

        return preferences

    async def opt_out_channel(
        self,
        patient_id: str,
        channel: str,
    ) -> CommunicationPreference:
        """
        Desabilita um canal específico (opt-out).

        Args:
            patient_id: ID do paciente
            channel: Canal a desabilitar (rocketchat, email, sms, whatsapp, push, jitsi)

        Returns:
            CommunicationPreference atualizado
        """
        channel_map = {
            "rocketchat": "rocketchat_enabled",
            "email": "email_enabled",
            "sms": "sms_enabled",
            "whatsapp": "whatsapp_enabled",
            "push": "push_enabled",
            "jitsi": "jitsi_enabled",
        }

        if channel not in channel_map:
            raise ValueError(f"Canal inválido: {channel}")

        kwargs = {channel_map[channel]: False}
        return await self.update_preferences(patient_id, **kwargs)

    async def opt_in_channel(
        self,
        patient_id: str,
        channel: str,
    ) -> CommunicationPreference:
        """
        Habilita um canal específico (opt-in).

        Args:
            patient_id: ID do paciente
            channel: Canal a habilitar (rocketchat, email, sms, whatsapp, push, jitsi)

        Returns:
            CommunicationPreference atualizado
        """
        channel_map = {
            "rocketchat": "rocketchat_enabled",
            "email": "email_enabled",
            "sms": "sms_enabled",
            "whatsapp": "whatsapp_enabled",
            "push": "push_enabled",
            "jitsi": "jitsi_enabled",
        }

        if channel not in channel_map:
            raise ValueError(f"Canal inválido: {channel}")

        kwargs = {channel_map[channel]: True}
        return await self.update_preferences(patient_id, **kwargs)

    async def grant_consent(
        self,
        patient_id: str,
        metadata: Optional[dict] = None,
    ) -> CommunicationPreference:
        """
        Concede consentimento para comunicações.

        Args:
            patient_id: ID do paciente
            metadata: Metadados do consentimento (IP, user agent, etc.)

        Returns:
            CommunicationPreference atualizado
        """
        preferences = await self.get_preferences(patient_id)

        if not preferences:
            preferences = await self.create_default_preferences(patient_id)

        # Atualizar preferências
        now = datetime.now()
        preferences.consent_given = True
        preferences.consent_given_at = now
        preferences.consent_version = self._config.consent_version
        preferences.consent_expires_at = now + timedelta(days=self._config.consent_renewal_days)

        # Registrar no log de consentimento
        consent_log = ConsentLogEntry(
            patient_id=patient_id,
            consent_status=ConsentStatus.GRANTED.value,
            consent_version=self._config.consent_version,
            consent_given_at=now,
            metadata=metadata or {},
        )

        self._db.add(consent_log)
        await self._db.commit()
        await self._db.refresh(preferences)

        return preferences

    async def withdraw_consent(
        self,
        patient_id: str,
        metadata: Optional[dict] = None,
    ) -> CommunicationPreference:
        """
        Revoga consentimento para comunicações.

        Args:
            patient_id: ID do paciente
            metadata: Metadados da revogação (IP, user agent, etc.)

        Returns:
            CommunicationPreference atualizado
        """
        preferences = await self.get_preferences(patient_id)

        if not preferences:
            preferences = await self.create_default_preferences(patient_id)

        # Atualizar preferências
        preferences.consent_given = False
        preferences.consent_given_at = None
        preferences.consent_version = None
        preferences.consent_expires_at = None

        # Registrar no log de consentimento
        consent_log = ConsentLogEntry(
            patient_id=patient_id,
            consent_status=ConsentStatus.WITHDRAWN.value,
            consent_version=self._config.consent_version,
            metadata=metadata or {},
        )

        self._db.add(consent_log)
        await self._db.commit()
        await self._db.refresh(preferences)

        return preferences

    async def get_consent_log(self, patient_id: str) -> list[ConsentLogEntry]:
        """
        Busca histórico de consentimento do paciente.

        Args:
            patient_id: ID do paciente

        Returns:
            Lista de ConsentLogEntry ordenada por data (mais recente primeiro)
        """
        stmt = (
            select(ConsentLogEntry)
            .where(ConsentLogEntry.patient_id == patient_id)
            .order_by(ConsentLogEntry.consent_given_at.desc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

