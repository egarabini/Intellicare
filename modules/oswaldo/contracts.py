from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class PrescriptionItem(BaseModel):
    drug: str
    posology: str
    duration: str | None = None
    notes: str | None = None


class OswaldoSuggestRequest(BaseModel):
    encounter_id: str | int
    patient_id: str | int
    chief_complaint: str
    recent_diagnoses: list[str] | None = None
    current_medications: list[str] | None = None


class OswaldoSuggestion(BaseModel):
    cid10_code: str
    cid10_desc: str
    prescription_items: list[PrescriptionItem]
    model: str
    confidence: str


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


class MedicationItem(BaseModel):
    order: int
    drug_name: str              
    concentration: str          
    pharmaceutical_form: str    
    quantity: int               
    quantity_unit: str          
    dosage_instructions: str    
    route: str                  

PrescriptionType = Literal["simple", "special_control"]

class ReceituarioData(BaseModel):
    prescription_id: str
    issued_at: datetime
    prescription_type: PrescriptionType

    professional_name: str
    crm: str
    crm_state: str
    specialty: str
    clinic_address: str
    clinic_phone: str

    patient_name: str
    patient_age: int
    patient_cpf: str | None = None

    cid10_code: str
    cid10_description: str
    medications: list[MedicationItem]

    prescription_validity_days: int | None = None
    prescription_number: str | None = None
