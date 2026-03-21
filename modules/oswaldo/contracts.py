from pydantic import BaseModel
from datetime import datetime


class PrescriptionItem(BaseModel):
    drug: str
    posology: str
    duration: str | None = None
    notes: str | None = None


class CreatePrescriptionRequest(BaseModel):
    encounter_id: str
    patient_id: str
    cid10_code: str | None = None
    cid10_desc: str | None = None
    items: list[PrescriptionItem] = []
    notes: str | None = None


class Prescription(BaseModel):
    id: int
    encounter_id: str
    patient_id: str
    author_id: str
    author_name: str
    cid10_code: str | None
    cid10_desc: str | None
    items: list[PrescriptionItem]
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class CID10Result(BaseModel):
    code: str
    description: str


class OswaldoSuggestRequest(BaseModel):
    encounter_id: int
    patient_id: int
    chief_complaint: str
    recent_diagnoses: list[str] | None = None
    current_medications: list[str] | None = None


class OswaldoSuggestion(BaseModel):
    cid10_code: str
    cid10_desc: str
    prescription_items: list[PrescriptionItem]
    model: str
    confidence: str
