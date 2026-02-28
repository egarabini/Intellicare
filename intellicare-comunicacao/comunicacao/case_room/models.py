"""Modelos de dados para Sala de Caso Multidisciplinar (EF-COM-021)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class CaseRoomStatus(str, Enum):
    """Status da sala de caso."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class CaseRoomMember(BaseModel):
    """Profissional membro da sala de caso."""

    professional_id: str = Field(..., description="ID Keycloak do profissional")
    username: str = Field(..., description="Username no Rocket.Chat")
    role: str = Field("professional", description="Papel: doctor, nurse, care_coordinator, etc.")
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CaseRoom(BaseModel):
    """Sala de caso clínico multidisciplinar."""

    patient_id: str
    patient_name: str | None = None
    rc_channel_id: str = Field("", description="ID do canal RC (_id)")
    rc_channel_name: str = Field("", description="Nome do canal RC (sem #)")
    rc_channel_type: str = Field("p", description="Tipo: p=grupo privado")
    members: list[CaseRoomMember] = Field(default_factory=list)
    status: CaseRoomStatus = CaseRoomStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_summary_at: datetime | None = None
    last_alert_at: datetime | None = None


class CreateCaseRoomRequest(BaseModel):
    """Request para criar sala de caso multidisciplinar."""

    patient_name: str | None = Field(None, description="Nome do paciente")
    professionals: list[CaseRoomMember] = Field(
        default_factory=list,
        description="Profissionais a adicionar (base: plano de cuidado Geralda)",
    )
    initial_summary: str | None = Field(None, description="Resumo clínico inicial a fixar no canal")

    class Config:
        json_schema_extra = {
            "example": {
                "patient_name": "Maria da Silva",
                "professionals": [
                    {"professional_id": "kc-user-1", "username": "dr.joao", "role": "doctor"},
                    {"professional_id": "kc-user-2", "username": "enf.ana", "role": "nurse"},
                ],
                "initial_summary": "DM2 + HAS + DRC G3a. Última eGFR: 45 ml/min/1.73m².",
            }
        }


class AddMemberRequest(BaseModel):
    """Request para adicionar membro à sala de caso."""

    professional_id: str = Field(..., description="ID Keycloak do profissional")
    username: str = Field(..., description="Username RC do profissional")
    role: str = Field("professional", description="Papel do profissional")


class PostSummaryRequest(BaseModel):
    """Request para fixar resumo clínico no canal."""

    summary: str = Field(..., min_length=1, description="Resumo clínico em Markdown")
    source_module: str = Field("wanda", description="Módulo que gerou o resumo")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "**Resumo Clínico** — Maria da Silva\n- DM2: HbA1c 9.2%\n- HAS: PA 155/95\n- DRC G3a: eGFR 45",
                "source_module": "wanda",
            }
        }


class PostAlertRequest(BaseModel):
    """Request para rotear alerta clínico ao canal da sala."""

    alert_text: str = Field(..., min_length=1, description="Texto do alerta clínico")
    severity: str = Field("medium", description="Severidade: critical, high, medium, low")
    source_module: str = Field("unknown", description="Módulo origem do alerta")

    class Config:
        json_schema_extra = {
            "example": {
                "alert_text": "eGFR caiu de 45 para 30 ml/min/1.73m² em 30 dias.",
                "severity": "high",
                "source_module": "intellicare-oswaldo",
            }
        }


class LaunchTeleconsultRequest(BaseModel):
    """Request para iniciar teleconsulta multidisciplinar na sala de caso."""

    initiator_id: str = Field(..., description="ID Keycloak do profissional que inicia")
    initiator_username: str = Field(..., description="Username RC do iniciador")
    duration_minutes: int = Field(30, ge=15, le=180, description="Duração prevista em minutos")

    class Config:
        json_schema_extra = {
            "example": {
                "initiator_id": "kc-user-123",
                "initiator_username": "dr.joao",
                "duration_minutes": 45,
            }
        }


class LaunchTeleconsultResponse(BaseModel):
    """Resposta ao lançar teleconsulta multidisciplinar."""

    patient_id: str
    jitsi_room_name: str
    jitsi_url: str
    notified_members: int
    initiated_by: str
    duration_minutes: int
