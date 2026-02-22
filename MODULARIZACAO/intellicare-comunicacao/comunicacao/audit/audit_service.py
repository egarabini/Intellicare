"""Serviço de trilha de auditoria."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.audit.hash_chain import HashChainManager
from comunicacao.audit.models import AuditEntry
from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import CommunicationPreference

if TYPE_CHECKING:
    from comunicacao.lgpd.models import LGPDDecision
    from comunicacao.routing.models import CommunicationIntentRecord, DeliveryResultRecord


class AuditTrailService:
    """
    Serviço de trilha de auditoria para comunicações.
    
    Cada comunicação gera uma entrada de audit imutável.
    Hash chain garante integridade (semelhante a blockchain simplificado).
    """
    
    def __init__(self, db: AsyncSession, config: LGPDConfig):
        self._db = db
        self._config = config
        self._hash_manager = HashChainManager()
    
    async def log_communication(
        self,
        intent: CommunicationIntentRecord,
        delivery: DeliveryResultRecord,
        lgpd_decision: LGPDDecision,
        patient_id: Optional[str] = None,
    ) -> AuditEntry:
        """
        Registra comunicação na trilha de auditoria.
        
        Chamado APÓS cada tentativa de envio (sucesso ou falha).
        
        Args:
            intent: Intenção de comunicação
            delivery: Resultado da entrega
            lgpd_decision: Decisão LGPD
            patient_id: ID do paciente (se aplicável)
        
        Returns:
            AuditEntry criado
        """
        # 1. Buscar hash do último audit entry (para chain)
        previous_hash = await self._get_last_hash()
        
        # 2. Hash pseudonimizado do recipient
        recipient_hash = self._hash_manager.hash_recipient(
            intent.recipient_id,
            self._config.anonymization_hash_salt,
        )
        
        # Hash do paciente (se fornecido)
        patient_hash = None
        if patient_id:
            patient_hash = self._hash_manager.hash_recipient(
                patient_id,
                self._config.anonymization_hash_salt,
            )
        
        # 3. Criar timestamp
        created_at = datetime.now()
        created_at_str = created_at.isoformat()
        
        # 4. Calcular hash do entry atual
        entry_hash = self._hash_manager.calculate_hash(
            intent_id=str(intent.id),
            delivery_id=str(delivery.id),
            intent_type=intent.category,
            channel=delivery.channel,
            recipient_hash=recipient_hash,
            status=delivery.status.value,
            legal_basis=lgpd_decision.legal_basis.value if lgpd_decision.legal_basis else None,
            lgpd_override=lgpd_decision.override_applied,
            severity=intent.severity,
            source_module=intent.source_module,
            previous_hash=previous_hash,
            created_at=created_at_str,
        )
        
        # 5. Criar AuditEntry
        entry = AuditEntry(
            intent_id=str(intent.id),
            delivery_id=str(delivery.id),
            intent_type=intent.category,
            template_name=intent.content_template_id,
            channel=delivery.channel,
            recipient_type=intent.recipient_type.value,
            recipient_hash=recipient_hash,
            patient_hash=patient_hash,
            status=delivery.status.value,
            error_message=delivery.error_message,
            legal_basis=lgpd_decision.legal_basis.value if lgpd_decision.legal_basis else None,
            lgpd_override=lgpd_decision.override_applied,
            lgpd_reason=lgpd_decision.reason,
            consent_status=None,  # TODO: buscar do preferences
            severity=intent.severity,
            source_module=intent.source_module,
            source_event_id=intent.source_event_id,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
            created_at=created_at,
            metadata={
                "correlation_id": intent.correlation_id,
                "attempt_number": delivery.attempt_number,
            },
        )
        
        # 6. Salvar entry (INSERT ONLY — nunca UPDATE)
        self._db.add(entry)
        await self._db.commit()
        await self._db.refresh(entry)
        
        return entry
    
    async def log_lgpd_decision(
        self,
        intent: CommunicationIntentRecord,
        decision: LGPDDecision,
        patient_id: Optional[str] = None,
    ) -> AuditEntry:
        """
        Registra decisão LGPD (quando comunicação é bloqueada ou adiada).
        
        Args:
            intent: Intenção de comunicação
            decision: Decisão LGPD
            patient_id: ID do paciente (se aplicável)
        
        Returns:
            AuditEntry criado
        """
        # 1. Buscar hash do último audit entry
        previous_hash = await self._get_last_hash()
        
        # 2. Hash pseudonimizado
        recipient_hash = self._hash_manager.hash_recipient(
            intent.recipient_id,
            self._config.anonymization_hash_salt,
        )
        
        patient_hash = None
        if patient_id:
            patient_hash = self._hash_manager.hash_recipient(
                patient_id,
                self._config.anonymization_hash_salt,
            )

        # 3. Criar timestamp
        created_at = datetime.now()
        created_at_str = created_at.isoformat()

        # 4. Determinar status
        status = "blocked_lgpd" if not decision.allowed else "deferred"

        # 5. Calcular hash do entry
        entry_hash = self._hash_manager.calculate_hash(
            intent_id=str(intent.id),
            delivery_id=None,
            intent_type=intent.category,
            channel="none",
            recipient_hash=recipient_hash,
            status=status,
            legal_basis=decision.legal_basis.value if decision.legal_basis else None,
            lgpd_override=decision.override_applied,
            severity=intent.severity,
            source_module=intent.source_module,
            previous_hash=previous_hash,
            created_at=created_at_str,
        )

        # 6. Criar AuditEntry
        entry = AuditEntry(
            intent_id=str(intent.id),
            delivery_id=None,
            intent_type=intent.category,
            template_name=intent.content_template_id,
            channel="none",
            recipient_type=intent.recipient_type.value,
            recipient_hash=recipient_hash,
            patient_hash=patient_hash,
            status=status,
            error_message=None,
            legal_basis=decision.legal_basis.value if decision.legal_basis else None,
            lgpd_override=decision.override_applied,
            lgpd_reason=decision.reason,
            consent_status=None,
            severity=intent.severity,
            source_module=intent.source_module,
            source_event_id=intent.source_event_id,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
            created_at=created_at,
            metadata={
                "correlation_id": intent.correlation_id,
                "deferred_until": decision.deferred_until.isoformat() if decision.deferred_until else None,
            },
        )

        # 7. Salvar entry
        self._db.add(entry)
        await self._db.commit()
        await self._db.refresh(entry)

        return entry

    async def get_audit_by_intent(self, intent_id: UUID) -> list[AuditEntry]:
        """
        Busca todas as entradas de audit para uma intent.

        Args:
            intent_id: ID da intent

        Returns:
            Lista de AuditEntry ordenada por created_at
        """
        stmt = (
            select(AuditEntry)
            .where(AuditEntry.intent_id == str(intent_id))
            .order_by(AuditEntry.created_at.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_audit_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """
        Busca entradas de audit para um paciente.

        Args:
            patient_id: ID do paciente
            limit: Número máximo de entradas

        Returns:
            Lista de AuditEntry ordenada por created_at (mais recente primeiro)
        """
        patient_hash = self._hash_manager.hash_recipient(
            patient_id,
            self._config.anonymization_hash_salt,
        )

        stmt = (
            select(AuditEntry)
            .where(AuditEntry.patient_hash == patient_hash)
            .order_by(AuditEntry.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def verify_chain_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verifica integridade da hash chain completa.

        Returns:
            Tupla (is_valid, error_message)
        """
        # Buscar todos os entries ordenados por created_at
        stmt = select(AuditEntry).order_by(AuditEntry.created_at.asc())
        result = await self._db.execute(stmt)
        entries = result.scalars().all()

        # Converter para dicts
        entries_dict = [
            {
                "id": str(entry.id),
                "intent_id": entry.intent_id,
                "delivery_id": entry.delivery_id,
                "intent_type": entry.intent_type,
                "channel": entry.channel,
                "recipient_hash": entry.recipient_hash,
                "status": entry.status,
                "legal_basis": entry.legal_basis,
                "lgpd_override": entry.lgpd_override,
                "severity": entry.severity,
                "source_module": entry.source_module,
                "previous_hash": entry.previous_hash,
                "entry_hash": entry.entry_hash,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ]

        return self._hash_manager.verify_chain_integrity(entries_dict)

    async def list_audit_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        channel: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        legal_basis: str | None = None,
        lgpd_override: bool | None = None,
        patient_id: str | None = None,
        source_module: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> tuple[int, list[AuditEntry]]:
        """Lista entradas de audit com filtros e paginação."""
        filters = []
        if channel:
            filters.append(AuditEntry.channel == channel)
        if status:
            filters.append(AuditEntry.status == status)
        if severity:
            filters.append(AuditEntry.severity == severity)
        if legal_basis:
            filters.append(AuditEntry.legal_basis == legal_basis)
        if lgpd_override is not None:
            filters.append(AuditEntry.lgpd_override == lgpd_override)
        if source_module:
            filters.append(AuditEntry.source_module == source_module)
        if from_dt:
            filters.append(AuditEntry.created_at >= from_dt)
        if to_dt:
            filters.append(AuditEntry.created_at <= to_dt)
        if patient_id:
            patient_hash = self._hash_manager.hash_recipient(
                patient_id,
                self._config.anonymization_hash_salt,
            )
            filters.append(AuditEntry.patient_hash == patient_hash)

        count_stmt = select(func.count()).select_from(AuditEntry)
        stmt = select(AuditEntry).order_by(AuditEntry.created_at.desc()).limit(limit).offset(offset)
        if filters:
            clause = and_(*filters)
            count_stmt = count_stmt.where(clause)
            stmt = stmt.where(clause)

        total = (await self._db.execute(count_stmt)).scalar_one()
        entries = list((await self._db.execute(stmt)).scalars().all())
        return int(total), entries

    async def compute_compliance_report(self, period: str) -> dict[str, object]:
        """Computa métricas agregadas de conformidade."""
        now = datetime.now(UTC)
        if period == "month":
            start = now - timedelta(days=30)
        elif period == "quarter":
            start = now - timedelta(days=90)
        else:
            start = now - timedelta(days=365)

        total_stmt = select(func.count()).select_from(AuditEntry).where(AuditEntry.created_at >= start)
        total = int((await self._db.execute(total_stmt)).scalar_one())

        legal_stmt = (
            select(AuditEntry.legal_basis, func.count())
            .where(and_(AuditEntry.created_at >= start, AuditEntry.legal_basis.is_not(None)))
            .group_by(AuditEntry.legal_basis)
        )
        by_legal_basis = {
            str(row[0]): int(row[1])
            for row in (await self._db.execute(legal_stmt)).all()
            if row[0] is not None
        }

        critical_overrides_stmt = select(func.count()).select_from(AuditEntry).where(
            and_(
                AuditEntry.created_at >= start,
                AuditEntry.severity == "critical",
                AuditEntry.lgpd_override.is_(True),
            )
        )
        critical_overrides = int((await self._db.execute(critical_overrides_stmt)).scalar_one())

        blocked_stmt = select(func.count()).select_from(AuditEntry).where(
            and_(AuditEntry.created_at >= start, AuditEntry.status == "blocked_lgpd")
        )
        blocked_by_lgpd = int((await self._db.execute(blocked_stmt)).scalar_one())

        prefs_total_stmt = select(func.count()).select_from(CommunicationPreference)
        prefs_total = int((await self._db.execute(prefs_total_stmt)).scalar_one())

        consent_stmt = select(func.count()).select_from(CommunicationPreference).where(
            CommunicationPreference.consent_given.is_(True)
        )
        consent_count = int((await self._db.execute(consent_stmt)).scalar_one())

        opt_out_stmt = select(func.count()).select_from(CommunicationPreference).where(
            or_(
                CommunicationPreference.rocketchat_enabled.is_(False),
                CommunicationPreference.email_enabled.is_(False),
                CommunicationPreference.sms_enabled.is_(False),
                CommunicationPreference.whatsapp_enabled.is_(False),
                CommunicationPreference.push_enabled.is_(False),
                CommunicationPreference.jitsi_enabled.is_(False),
            )
        )
        opt_out_count = int((await self._db.execute(opt_out_stmt)).scalar_one())

        chain_integrity, _ = await self.verify_chain_integrity()

        return {
            "total_communications": total,
            "by_legal_basis": by_legal_basis,
            "critical_overrides": critical_overrides,
            "blocked_by_lgpd": blocked_by_lgpd,
            "opt_out_rate": (opt_out_count / prefs_total) if prefs_total else 0.0,
            "consent_coverage": (consent_count / prefs_total) if prefs_total else 0.0,
            "chain_integrity": chain_integrity,
        }

    async def _get_last_hash(self) -> Optional[str]:
        """Busca hash do último audit entry."""
        stmt = (
            select(AuditEntry.entry_hash)
            .order_by(AuditEntry.created_at.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
