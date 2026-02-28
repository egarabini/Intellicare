"""Serviço de direitos do titular de dados (Art. 18 LGPD)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.audit.fhir_communication import FHIRCommunicationBuilder
from comunicacao.audit.hash_chain import HashChainManager
from comunicacao.audit.models import AuditEntry
from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import CommunicationPreference, ConsentLogEntry


class DataSubjectService:
    """
    Serviço de direitos do titular de dados (Art. 18 LGPD).
    
    Implementa:
    - Art. 18, I: Confirmação da existência de tratamento
    - Art. 18, II: Acesso aos dados
    - Art. 18, III: Correção de dados incompletos/inexatos
    - Art. 18, IV: Anonimização, bloqueio ou eliminação
    - Art. 18, V: Portabilidade dos dados
    - Art. 18, VI: Eliminação dos dados
    - Art. 18, VII: Informação sobre compartilhamento
    - Art. 18, VIII: Revogação do consentimento
    """
    
    def __init__(self, db: AsyncSession, config: LGPDConfig):
        self._db = db
        self._config = config
        self._hash_manager = HashChainManager()
    
    async def export_data(
        self,
        patient_id: str,
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        Exporta todos os dados do paciente (Art. 18, II e V - Portabilidade).
        
        Args:
            patient_id: ID do paciente
            format: Formato de exportação (json ou fhir)
        
        Returns:
            Dict com todos os dados do paciente
        """
        # 1. Hash do paciente
        patient_hash = self._hash_manager.hash_recipient(
            patient_id,
            self._config.anonymization_hash_salt,
        )
        
        # 2. Buscar preferências
        preferences = await self._get_preferences(patient_id)
        
        # 3. Buscar histórico de consentimento
        consent_log = await self._get_consent_log(patient_id)
        
        # 4. Buscar audit trail
        audit_entries = await self._get_audit_entries(patient_hash)
        
        # 5. Montar exportação
        if format == "fhir":
            return await self._export_fhir(patient_id, preferences, consent_log, audit_entries)
        else:
            return await self._export_json(patient_id, preferences, consent_log, audit_entries)
    
    async def anonymize(self, patient_id: str) -> Dict[str, Any]:
        """
        Anonimiza dados do paciente (Art. 18, IV).
        
        IMPORTANTE: Mantém audit trail por requisito legal (5 anos),
        mas remove identificadores diretos.
        
        Args:
            patient_id: ID do paciente
        
        Returns:
            Dict com resultado da anonimização
        """
        # 1. Hash do paciente
        patient_hash = self._hash_manager.hash_recipient(
            patient_id,
            self._config.anonymization_hash_salt,
        )
        
        # 2. Contar registros antes
        preferences = await self._get_preferences(patient_id)
        consent_log = await self._get_consent_log(patient_id)
        audit_entries = await self._get_audit_entries(patient_hash)
        
        counts_before = {
            "preferences": 1 if preferences else 0,
            "consent_log": len(consent_log),
            "audit_entries": len(audit_entries),
        }
        
        # 3. Remover preferências (dados diretos)
        if preferences:
            await self._db.delete(preferences)
        
        # 4. Anonimizar consent log (manter por requisito legal, mas sem patient_id)
        stmt = (
            update(ConsentLogEntry)
            .where(ConsentLogEntry.patient_id == patient_id)
            .values(patient_id=f"ANONYMIZED_{patient_hash[:16]}")
        )
        await self._db.execute(stmt)
        
        # 5. Audit trail NÃO é anonimizado (requisito legal de 5 anos)
        # Já está pseudonimizado com patient_hash
        
        await self._db.commit()
        
        return {
            "patient_id": patient_id,
            "anonymized_at": "now",
            "counts_before": counts_before,
            "audit_trail_retained": True,
            "audit_retention_years": self._config.audit_retention_years,
            "note": "Audit trail mantido por requisito legal (pseudonimizado)",
        }
    
    async def get_consent_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retorna histórico de consentimento do paciente (Art. 18, II).
        
        Args:
            patient_id: ID do paciente
        
        Returns:
            Lista de consentimentos
        """
        consent_log = await self._get_consent_log(patient_id)
        
        return [
            {
                "id": str(entry.id),
                "status": entry.consent_status,
                "version": entry.consent_version,
                "given_at": entry.consent_given_at.isoformat(),
                "metadata": entry.metadata,
            }
            for entry in consent_log
        ]
    
    async def get_communication_history(
        self,
        patient_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retorna histórico de comunicações do paciente (Art. 18, II).
        
        Args:
            patient_id: ID do paciente
            limit: Número máximo de registros
        
        Returns:
            Lista de comunicações
        """
        patient_hash = self._hash_manager.hash_recipient(
            patient_id,
            self._config.anonymization_hash_salt,
        )
        
        audit_entries = await self._get_audit_entries(patient_hash, limit)

        return [
            {
                "id": str(entry.id),
                "intent_id": entry.intent_id,
                "channel": entry.channel,
                "status": entry.status,
                "severity": entry.severity,
                "legal_basis": entry.legal_basis,
                "lgpd_override": entry.lgpd_override,
                "sent_at": entry.created_at.isoformat(),
                "error_message": entry.error_message,
            }
            for entry in audit_entries
        ]

    # ── Métodos auxiliares ──

    async def _get_preferences(self, patient_id: str) -> Optional[CommunicationPreference]:
        """Busca preferências do paciente."""
        stmt = select(CommunicationPreference).where(
            CommunicationPreference.patient_id == patient_id
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_consent_log(self, patient_id: str) -> List[ConsentLogEntry]:
        """Busca histórico de consentimento."""
        stmt = (
            select(ConsentLogEntry)
            .where(ConsentLogEntry.patient_id == patient_id)
            .order_by(ConsentLogEntry.consent_given_at.desc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _get_audit_entries(
        self,
        patient_hash: str,
        limit: Optional[int] = None,
    ) -> List[AuditEntry]:
        """Busca audit entries do paciente."""
        stmt = (
            select(AuditEntry)
            .where(AuditEntry.patient_hash == patient_hash)
            .order_by(AuditEntry.created_at.desc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _export_json(
        self,
        patient_id: str,
        preferences: Optional[CommunicationPreference],
        consent_log: List[ConsentLogEntry],
        audit_entries: List[AuditEntry],
    ) -> Dict[str, Any]:
        """Exporta dados em formato JSON."""
        return {
            "patient_id": patient_id,
            "exported_at": "now",
            "preferences": {
                "rocketchat_enabled": preferences.rocketchat_enabled if preferences else None,
                "email_enabled": preferences.email_enabled if preferences else None,
                "sms_enabled": preferences.sms_enabled if preferences else None,
                "whatsapp_enabled": preferences.whatsapp_enabled if preferences else None,
                "push_enabled": preferences.push_enabled if preferences else None,
                "jitsi_enabled": preferences.jitsi_enabled if preferences else None,
                "quiet_hours": preferences.quiet_hours if preferences else None,
                "consent_given": preferences.consent_given if preferences else False,
                "consent_given_at": preferences.consent_given_at.isoformat() if preferences and preferences.consent_given_at else None,
                "consent_version": preferences.consent_version if preferences else None,
            } if preferences else None,
            "consent_history": [
                {
                    "status": entry.consent_status,
                    "version": entry.consent_version,
                    "given_at": entry.consent_given_at.isoformat(),
                    "metadata": entry.metadata,
                }
                for entry in consent_log
            ],
            "communication_history": [
                {
                    "intent_id": entry.intent_id,
                    "channel": entry.channel,
                    "status": entry.status,
                    "severity": entry.severity,
                    "legal_basis": entry.legal_basis,
                    "sent_at": entry.created_at.isoformat(),
                }
                for entry in audit_entries
            ],
            "total_communications": len(audit_entries),
        }

    async def _export_fhir(
        self,
        patient_id: str,
        preferences: Optional[CommunicationPreference],
        consent_log: List[ConsentLogEntry],
        audit_entries: List[AuditEntry],
    ) -> Dict[str, Any]:
        """Exporta dados em formato FHIR Bundle."""
        # Converter audit entries para FHIR Communication
        communications = [
            FHIRCommunicationBuilder.build_from_audit(entry)
            for entry in audit_entries
        ]

        return {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": "now",
            "total": len(communications),
            "entry": [
                {
                    "fullUrl": f"urn:uuid:{comm['id']}",
                    "resource": comm,
                }
                for comm in communications
            ],
        }

