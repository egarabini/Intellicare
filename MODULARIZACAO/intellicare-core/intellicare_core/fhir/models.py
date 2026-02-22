"""Modelos FHIR simplificados para uso nos modulos IntelliCare.

Estes modelos sao wrappers leves sobre os recursos FHIR R4, otimizados
para o contexto de agentes de saude. Para acesso ao recurso FHIR completo,
usar fhir.resources diretamente.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class ObservationValue(BaseModel):
    """Valor de uma observacao clinica (exame, sinal vital, etc.)."""

    code: str = Field(..., description="Codigo LOINC ou local")
    display: str = Field(default="", description="Nome legivel")
    value: float | None = None
    unit: str = ""
    date: datetime | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    interpretation: str = Field(default="", description="normal | high | low | critical")

    @property
    def is_abnormal(self) -> bool:
        if self.reference_low is not None and self.value is not None:
            if self.value < self.reference_low:
                return True
        if self.reference_high is not None and self.value is not None:
            if self.value > self.reference_high:
                return True
        return False


class ConditionSummary(BaseModel):
    """Resumo de uma condicao clinica (diagnostico)."""

    code: str = Field(..., description="Codigo CID-10 ou SNOMED")
    display: str = ""
    clinical_status: str = Field(default="active", description="active | resolved | inactive")
    onset_date: date | None = None
    category: str = ""


class AllergySummary(BaseModel):
    """Resumo de uma alergia."""

    substance: str = ""
    reaction: str = ""
    severity: str = Field(default="", description="low | high | unable-to-assess")
    clinical_status: str = "active"


class MedicationSummary(BaseModel):
    """Resumo de uma medicacao em uso."""

    name: str = ""
    code: str = ""
    dosage: str = ""
    frequency: str = ""
    status: str = Field(default="active", description="active | stopped | on-hold")


class PatientSummary(BaseModel):
    """Resumo consolidado de um paciente — usado por todos os agentes.

    Baseado no International Patient Summary (IPS Brasil).
    """

    patient_id: str = Field(..., description="ID FHIR do paciente")
    name: str = ""
    birth_date: date | None = None
    gender: str = ""
    cpf: str = ""

    # Dados clinicos
    conditions: list[ConditionSummary] = Field(default_factory=list)
    allergies: list[AllergySummary] = Field(default_factory=list)
    medications: list[MedicationSummary] = Field(default_factory=list)
    observations: list[ObservationValue] = Field(default_factory=list)

    @property
    def age(self) -> int | None:
        if self.birth_date is None:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def active_conditions(self) -> list[ConditionSummary]:
        return [c for c in self.conditions if c.clinical_status == "active"]

    @property
    def active_medications(self) -> list[MedicationSummary]:
        return [m for m in self.medications if m.status == "active"]

    def get_latest_observation(self, code: str) -> ObservationValue | None:
        """Retorna a observacao mais recente para um codigo LOINC."""
        matching = [o for o in self.observations if o.code == code]
        if not matching:
            return None
        return max(matching, key=lambda o: o.date or datetime.min)
