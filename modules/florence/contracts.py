from enum import StrEnum
from pydantic import BaseModel
from datetime import datetime


class NoteType(StrEnum):
    FREE = "FREE"
    SOAP = "SOAP"


class CreateNoteRequest(BaseModel):
    encounter_id: str | int
    patient_id: str | int
    note_type: NoteType = NoteType.FREE
    soap_s: str | None = None
    soap_o: str | None = None
    soap_a: str | None = None
    soap_p: str | None = None
    free_text: str | None = None


class ClinicalNote(BaseModel):
    id: int
    encounter_id: str | int | None
    patient_id: str | int | None
    author_id: str
    author_name: str
    note_type: NoteType
    soap_s: str | None
    soap_o: str | None
    soap_a: str | None
    soap_p: str | None
    free_text: str | None
    created_at: datetime
    updated_at: datetime


class SuggestRequest(BaseModel):
    encounter_id: str | int
    patient_id: str | int
    chief_complaint: str
    appointment_reason: str | None = None
    recent_notes: list[str] | None = None


class SOAPSuggestion(BaseModel):
    soap_s: str
    soap_o: str
    soap_a: str
    soap_p: str
    model: str
    confidence: str
