"""Adapter para integrar LGPDComplianceService com RoutingEngine."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from comunicacao.audit.audit_service import AuditTrailService
from comunicacao.lgpd.compliance_service import LGPDComplianceService
from comunicacao.lgpd.config import LGPDConfig
from comunicacao.routing.lgpd import LGPDDecision

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    
    from comunicacao.dispatchers.base import ResolvedRecipient
    from comunicacao.routing.models import CommunicationIntentRecord

logger = logging.getLogger(__name__)


class LGPDComplianceAdapter:
    """
    Adapter que integra LGPDComplianceService (D6) com RoutingEngine (D1).
    
    Responsabilidades:
    - Verificar conformidade LGPD antes de routing
    - Logar decisões LGPD em audit trail
    - Converter LGPDDecision (D6) para formato esperado pelo RoutingEngine
    - Tratar bloqueios e overrides
    """
    
    def __init__(
        self,
        db: AsyncSession,
        config: LGPDConfig | None = None,
    ) -> None:
        """
        Inicializa adapter.
        
        Args:
            db: Sessão do banco de dados
            config: Configuração LGPD (opcional, usa padrão se não fornecido)
        """
        self._db = db
        self._config = config or LGPDConfig.from_env()
        self._compliance_service = LGPDComplianceService(db, self._config)
        self._audit_service = AuditTrailService(db, self._config)
    
    async def can_send(
        self,
        patient_id: str,
        channel: str,
        intent_type: str,
        severity: str,
    ) -> LGPDDecision:
        """
        Verifica se pode enviar comunicação por canal específico.
        
        NOTA: Este método é mantido para compatibilidade com D1,
        mas recomenda-se usar check_compliance() que é mais completo.
        
        Args:
            patient_id: ID do paciente
            channel: Canal de comunicação
            intent_type: Tipo de intent
            severity: Severidade
        
        Returns:
            LGPDDecision com resultado da verificação
        """
        # Criar intent mock para verificação
        from comunicacao.routing.models import CommunicationIntentRecord, RecipientType
        
        mock_intent = CommunicationIntentRecord(
            source_module="lgpd_adapter",
            recipient_type=RecipientType.PATIENT,
            recipient_id=patient_id,
            severity=severity,
            category=intent_type,
            correlation_id=f"lgpd_check_{patient_id}_{channel}",
        )
        
        # Verificar compliance
        decision = await self._compliance_service.check_compliance(mock_intent, channel)
        
        # Converter para formato esperado pelo RoutingEngine
        return LGPDDecision(
            allowed=decision.allowed,
            legal_basis=decision.legal_basis.value if decision.legal_basis else None,
            reason=decision.reason,
            override_applied=decision.override_applied,
            defer_until=decision.deferred_until,
        )
    
    async def check_compliance(
        self,
        intent: CommunicationIntentRecord,
        resolved_recipient: ResolvedRecipient,
    ) -> bool:
        """
        Verifica conformidade LGPD para a intent.
        
        Este é o método principal usado pelo RoutingEngine.
        
        Args:
            intent: Intent de comunicação
            resolved_recipient: Destinatário resolvido
        
        Returns:
            True se permitido, False caso contrário
        """
        # Determinar patient_id
        patient_id = self._extract_patient_id(intent, resolved_recipient)
        
        # Verificar compliance para cada canal preferencial
        # Por enquanto, verificamos apenas o canal preferencial ou primeiro canal disponível
        channel = intent.preferred_channel or "rocketchat"  # Default
        
        try:
            decision = await self._compliance_service.check_compliance(intent, channel)
            
            # Logar decisão LGPD em audit trail
            await self._audit_service.log_lgpd_decision(
                intent=intent,
                decision=decision,
                patient_id=patient_id,
            )
            
            # Se bloqueado, logar warning
            if not decision.allowed:
                logger.warning(
                    "LGPD: Intent %s bloqueado - %s (patient=%s, channel=%s)",
                    intent.id,
                    decision.reason,
                    patient_id,
                    channel,
                )
            
            # Se override aplicado, logar info
            if decision.override_applied:
                logger.info(
                    "LGPD: Intent %s com override - %s (patient=%s, channel=%s, legal_basis=%s)",
                    intent.id,
                    decision.reason,
                    patient_id,
                    channel,
                    decision.legal_basis.value if decision.legal_basis else "none",
                )
            
            return decision.allowed
            
        except Exception as e:
            logger.error(
                "LGPD: Erro ao verificar compliance para intent %s: %s",
                intent.id,
                str(e),
                exc_info=True,
            )
            # Em caso de erro, bloquear por segurança (fail-safe)
            return False
    
    def _extract_patient_id(
        self,
        intent: CommunicationIntentRecord,
        resolved_recipient: ResolvedRecipient,
    ) -> str | None:
        """
        Extrai patient_id da intent ou do recipient resolvido.
        
        Args:
            intent: Intent de comunicação
            resolved_recipient: Destinatário resolvido
        
        Returns:
            patient_id ou None se não for paciente
        """
        # Se recipient_type é PATIENT, usar recipient_id
        if intent.recipient_type.value == "patient":
            return intent.recipient_id
        
        # Caso contrário, tentar extrair de resolved_recipient
        # (pode ter patient_id em metadata)
        if hasattr(resolved_recipient, "patient_id"):
            return resolved_recipient.patient_id
        
        return None

