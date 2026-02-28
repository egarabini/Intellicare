"""Typed models extracted from a CCDA document."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    identifiers: list[dict[str, Any]] = Field(default_factory=list)
    name: dict[str, Any] = Field(default_factory=dict)
    gender: str = "unknown"
    birth_date: str | None = None
    race: dict[str, Any] | None = None
    address: dict[str, Any] | None = None
    phone: dict[str, Any] | None = None


class ConditionInfo(BaseModel):
    code: dict[str, Any] = Field(default_factory=dict)
    status: str = "unknown"
    onset: str | None = None
    severity: dict[str, Any] | None = None


class MedicationInfo(BaseModel):
    medication_code: dict[str, Any] = Field(default_factory=dict)
    dosage: dict[str, Any] = Field(default_factory=dict)
    route: dict[str, Any] | None = None
    frequency: dict[str, Any] | None = None
    status: str = "active"


class ObservationInfo(BaseModel):
    code: dict[str, Any] = Field(default_factory=dict)
    value: dict[str, Any] | None = None
    unit: str | None = None
    effective: str | None = None
    reference_range: dict[str, Any] | None = None
    status: str = "final"


class ProcedureInfo(BaseModel):
    code: dict[str, Any] = Field(default_factory=dict)
    performed: str | None = None
    status: str = "completed"


class ImmunizationInfo(BaseModel):
    vaccine_code: dict[str, Any] = Field(default_factory=dict)
    occurrence: str | None = None
    lot_number: str | None = None
    expiration: str | None = None
    status: str = "completed"


class EncounterInfo(BaseModel):
    class_code: dict[str, Any] = Field(default_factory=dict)
    period: dict[str, Any] = Field(default_factory=dict)
    location: dict[str, Any] | None = None
    discharge_disposition: dict[str, Any] | None = None
    status: str = "finished"


class CCDADocument(BaseModel):
    source_document_id: str | None = None
    patient: PatientInfo
    conditions: list[ConditionInfo] = Field(default_factory=list)
    medications: list[MedicationInfo] = Field(default_factory=list)
    observations: list[ObservationInfo] = Field(default_factory=list)
    procedures: list[ProcedureInfo] = Field(default_factory=list)
    immunizations: list[ImmunizationInfo] = Field(default_factory=list)
    encounters: list[EncounterInfo] = Field(default_factory=list)
