"""Tipos de evento da jornada do paciente.

Define a estrutura padronizada IntelliCareEvent e catálogo de tipos.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Optional
from uuid import uuid4


# Enum de tipos de evento (catálogo)
class EventType:
    """Catálogo de tipos de evento IntelliCare."""

    # ===== Eventos Clínicos (prefixo: clinical.) =====
    ADMISSION = "clinical.admission"
    DISCHARGE = "clinical.discharge"
    CONDITION_DIAGNOSED = "clinical.condition_diagnosed"
    CONDITION_WORSENED = "clinical.condition_worsened"
    CONDITION_IMPROVED = "clinical.condition_improved"
    EXAM_RESULT = "clinical.exam_result"
    MEDICATION_CHANGED = "clinical.medication_changed"
    VITAL_SIGN_ALERT = "clinical.vital_sign_alert"

    # ===== Eventos de Cuidado (prefixo: care.) =====
    PLAN_CREATED = "care.plan_created"
    PLAN_UPDATED = "care.plan_updated"
    TASK_COMPLETED = "care.task_completed"
    TASK_MISSED = "care.task_missed"
    ADHERENCE_LOW = "care.adherence_low"
    ADHERENCE_IMPROVED = "care.adherence_improved"
    REMINDER_SENT = "care.reminder_sent"
    REMINDER_ACKNOWLEDGED = "care.reminder_acknowledged"

    # ===== Eventos Digitais (prefixo: digital.) =====
    PATIENT_ONBOARDED = "digital.patient_onboarded"
    MESSAGE_RECEIVED = "digital.message_received"
    MESSAGE_READ = "digital.message_read"
    CONSENT_GIVEN = "digital.consent_given"
    PREFERENCE_UPDATED = "digital.preference_updated"
    EDUCATION_COMPLETED = "digital.education_completed"
    QUIZ_COMPLETED = "digital.quiz_completed"

    # ===== Eventos Operacionais (prefixo: operational.) =====
    CONSULTATION_SCHEDULED = "operational.consultation_scheduled"
    CONSULTATION_COMPLETED = "operational.consultation_completed"
    CONSULTATION_MISSED = "operational.consultation_missed"
    TELECONSULT_SCHEDULED = "operational.teleconsult_scheduled"
    TELECONSULT_COMPLETED = "operational.teleconsult_completed"
    DISCHARGE_PLANNED = "operational.discharge_planned"
    REFERRAL_MADE = "operational.referral_made"


EVENT_CATALOG: dict[str, dict[str, str]] = {
    EventType.ADMISSION: {"description": "Admissao do paciente"},
    EventType.DISCHARGE: {"description": "Alta do paciente"},
    EventType.CONDITION_DIAGNOSED: {"description": "Condicao clinica diagnosticada"},
    EventType.CONDITION_WORSENED: {"description": "Piora da condicao clinica"},
    EventType.CONDITION_IMPROVED: {"description": "Melhora da condicao clinica"},
    EventType.EXAM_RESULT: {"description": "Resultado de exame recebido"},
    EventType.MEDICATION_CHANGED: {"description": "Mudanca de medicacao"},
    EventType.VITAL_SIGN_ALERT: {"description": "Alerta de sinal vital"},
    EventType.PLAN_CREATED: {"description": "Plano de cuidado criado"},
    EventType.PLAN_UPDATED: {"description": "Plano de cuidado atualizado"},
    EventType.TASK_COMPLETED: {"description": "Tarefa de cuidado concluida"},
    EventType.TASK_MISSED: {"description": "Tarefa de cuidado perdida"},
    EventType.ADHERENCE_LOW: {"description": "Adesao baixa detectada"},
    EventType.ADHERENCE_IMPROVED: {"description": "Melhora de adesao detectada"},
    EventType.REMINDER_SENT: {"description": "Lembrete enviado"},
    EventType.REMINDER_ACKNOWLEDGED: {"description": "Lembrete confirmado"},
    EventType.PATIENT_ONBOARDED: {"description": "Paciente onboarded na plataforma"},
    EventType.MESSAGE_RECEIVED: {"description": "Mensagem recebida"},
    EventType.MESSAGE_READ: {"description": "Mensagem lida"},
    EventType.CONSENT_GIVEN: {"description": "Consentimento registrado"},
    EventType.PREFERENCE_UPDATED: {"description": "Preferencias atualizadas"},
    EventType.EDUCATION_COMPLETED: {"description": "Conteudo educativo concluido"},
    EventType.QUIZ_COMPLETED: {"description": "Quiz concluido"},
    EventType.CONSULTATION_SCHEDULED: {"description": "Consulta agendada"},
    EventType.CONSULTATION_COMPLETED: {"description": "Consulta concluida"},
    EventType.CONSULTATION_MISSED: {"description": "Consulta perdida"},
    EventType.TELECONSULT_SCHEDULED: {"description": "Teleconsulta agendada"},
    EventType.TELECONSULT_COMPLETED: {"description": "Teleconsulta concluida"},
    EventType.DISCHARGE_PLANNED: {"description": "Planejamento de alta"},
    EventType.REFERRAL_MADE: {"description": "Encaminhamento realizado"},
}


def validate_event_type(event_type: str) -> bool:
    """Valida se o tipo de evento existe no catalogo."""
    return event_type in EVENT_CATALOG


def get_event_category(event_type: str) -> Optional[str]:
    """Retorna categoria (prefixo) do evento quando valido."""
    if not validate_event_type(event_type):
        return None
    return event_type.split(".", 1)[0]


@dataclass
class IntelliCareEvent:
    """
    Evento padrao da jornada do paciente.

    Estrutura única para todos os eventos do sistema IntelliCare,
    permitindo processamento normalizado pelo pipeline.
    """

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""  # ex: "care.plan_created"
    source: str = "geralda"  # ex: "geralda", "oswaldo", "florence", "manual"
    patient_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None  # Para rastrear cadeia de eventos
    idempotency_key: str = ""  # Chave para deduplicação
    metadata: dict[str, Any] = field(default_factory=dict)  # user_id, ip, etc.

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=UTC)
        if not self.idempotency_key:
            self.idempotency_key = create_idempotency_key(
                self.event_type,
                self.patient_id,
                self.payload if isinstance(self.payload, dict) else {},
            )

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário (para serialização JSON)."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "patient_id": self.patient_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntelliCareEvent":
        """Cria evento a partir de dicionário (deserialização JSON)."""
        return cls(
            event_id=data.get("event_id", str(uuid4())),
            event_type=data.get("event_type", ""),
            source=data.get("source", "unknown"),
            patient_id=data.get("patient_id", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(UTC),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id"),
            idempotency_key=data.get("idempotency_key", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ProcessingResult:
    """Resultado do processamento de um evento."""

    event_id: str
    status: str  # "processed", "skipped", "failed", "duplicate"
    context_activated: Optional[str] = None  # Contexto MCP ativado
    protocol_executed: Optional[str] = None  # Protocolo executado
    actions_taken: list[dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    processing_duration_ms: Optional[int] = None

    def __post_init__(self) -> None:
        if self.error_message and "error" not in self.error_message.lower():
            self.error_message = f"error: {self.error_message}"

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário."""
        return {
            "event_id": self.event_id,
            "status": self.status,
            "context_activated": self.context_activated,
            "protocol_executed": self.protocol_executed,
            "actions_taken": self.actions_taken,
            "error_message": self.error_message,
            "processing_duration_ms": self.processing_duration_ms,
        }


def create_idempotency_key(event_type: str, patient_id: str, payload: dict) -> str:
    """
    Gera chave de idempotência para o evento.

    Args:
        event_type: Tipo do evento
        patient_id: ID do paciente
        payload: Payload do evento

    Returns:
        Chave única para deduplicação
    """
    import hashlib
    import json

    # Ordena payload para consistência
    payload_str = json.dumps(payload, sort_keys=True)

    # Gera hash
    key_content = f"{event_type}:{patient_id}:{payload_str}"
    return hashlib.sha256(key_content.encode()).hexdigest()


# Função auxiliar para criar eventos
def emit_event(
    event_type: str,
    patient_id: str,
    payload: dict[str, Any],
    source: str = "geralda",
    correlation_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> IntelliCareEvent:
    """
    Cria um novo evento IntelliCare.

    Args:
        event_type: Tipo do evento (use EventType constants)
        patient_id: ID do paciente
        payload: Dados específicos do evento
        source: Origem do evento
        correlation_id: ID para correlacionar com outros eventos
        metadata: Metadados adicionais

    Returns:
        IntelliCareEvent criado
    """
    event = IntelliCareEvent(
        event_type=event_type,
        patient_id=patient_id,
        payload=payload,
        source=source,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )

    # Gera chave de idempotência
    event.idempotency_key = create_idempotency_key(
        event_type,
        patient_id,
        payload,
    )

    return event
